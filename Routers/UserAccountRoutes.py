# -----------------------------------------------------------
#  imports
# -----------------------------------------------------------
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta
from uuid import uuid4
import secrets            
from Database.Schemas.UserSchema import *                   # <── NEW
from passlib.context import CryptContext
from UserAccounts.UserWatchlistManagement import * 
from Database.databaseconfig import SessionLocal
from Database.models import User                     # whatever path your models live in
import sys

def get_deep_size(obj, seen=None):
    """Recursively calculate the size of a Python object in bytes."""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum(get_deep_size(k, seen) + get_deep_size(v, seen) for k, v in obj.items())
    elif hasattr(obj, '__dict__'):
        size += get_deep_size(vars(obj), seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum(get_deep_size(i, seen) for i in obj)
    return size


SECRET_KEY = "your‑secret‑key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")
router = APIRouter(prefix="/user", tags=["auth"])


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def generate_api_key() -> str:              
    return secrets.token_urlsafe(44)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return None
    return user

DATA_FETCHED_MB = 0.5
from datetime import date 
def track_read_and_data_usage(db: Session, user_id: str, data_obj, read_increment: int = 1):
    today = date.today()
    size_in_bytes = get_deep_size(data_obj)
    size_in_mb = round(size_in_bytes / (1024 * 1024), 4)

    from Database.models import ReadHistory  # avoid circular import if needed
    today = date.today().isoformat()
    record = db.query(ReadHistory).filter_by(user_id=user_id, date=today).first()
    
    if record:
        record.dataused += size_in_mb
    else:
        record = ReadHistory(user_id=user_id, reads=read_increment, dataused=size_in_mb, date=today)
        db.add(record)
    
    db.commit()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    cred_exc = HTTPException(status_code=401, detail="Invalid authentication credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise cred_exc
    except JWTError:
        raise cred_exc
      # Converts to 'YYYY-MM-DD' string
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise cred_exc

    # Track reads and data usage
    today = date.today().isoformat()
    read_record = db.query(ReadHistory).filter_by(user_id=user.id, date=str(today)).first()

    if read_record:
        read_record.reads += 1
    else:
        new_read = ReadHistory(
            user_id=user.id,
            reads=1,

            date=today
        )
        db.add(new_read)

    db.commit()

    return user

class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    email: EmailStr
    phonenumber: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str

class ApiKeyOut(BaseModel):
    api_key: str

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def generate_api_key() -> str:
    return secrets.token_urlsafe(44)  # ≈ 256 bits of entropy

@router.post("/signup", response_model=ApiKeyOut)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    api_key = generate_api_key()

    # Create the user
    new_user = User(
        id=str(uuid4()),
        username=user_in.username,
        password=hash_password(user_in.password),
        name=user_in.name,
        email=user_in.email,
        phonenumber=user_in.phonenumber,
        reads=0,
        Dataused=0.0,
        AuthToken=api_key,
        Apikey=generate_api_key()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    usage_entry = ApiKeyUsage(
        id=str(uuid4()),
        user_id=new_user.id,
        apikey=api_key,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    db.add(usage_entry)
    db.commit()
    return {"api_key": new_user.Apikey}


@router.post("/token", response_model=TokenOut)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    user.AuthToken = token
    db.commit()
    db.refresh(user)  # optional

    return {"access_token": token, "token_type": "bearer"}


@router.post("/refresh-api-key")
def refresh_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_key = generate_api_key()
    
    # Update user
    db_user = db.query(User).filter(User.id == current_user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.Apikey = new_key

    # Add to ApiKeyUsage
    key_usage = ApiKeyUsage(
        id=str(uuid4()),
        user_id=current_user.id,
        apikey=new_key,
        date=date.today()
    )
    db.add(key_usage)

    db.commit()
    db.refresh(db_user)

    return {"api_key": new_key}


@router.get("/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "name": current_user.name,
        "api_key": current_user.Apikey , 
        "id" : current_user.id
    }

@router.post("/add")
def add_to_watchlist(data: WatchlistPostSchema, db: Session = Depends(get_db)  , current_user: User = Depends(get_current_user)):
    if current_user.id == data.user_id : 
     result = AddStockToWatchlist(data.stock_id, data.user_id, db)
     if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    else  :   
         raise HTTPException(status_code=400, detail = "Permission Denied" )
    
    return result

@router.delete("/remove")
def remove_from_watchlist(data: WatchlistPostSchema, db: Session = Depends(get_db)  , current_user: User = Depends(get_current_user)):
    if current_user.id == data.user_id : 
        result = RemoveStockFromWatchlist(data.stock_id, data.user_id, db)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
    else :   
         raise HTTPException(status_code=400, detail = "Permission Denied" )
    return result


@router.get("/{user_id}", response_model=UserWithAllDataSchema)
def get_user_details(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user