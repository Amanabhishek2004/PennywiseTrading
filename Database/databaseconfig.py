from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import Header, HTTPException, Depends 
from sqlalchemy.orm import Session


# Make sure the special characters like `@` in password are URL-encoded
# `@` becomes `%40`, so `AMAN@2004` becomes `AMAN%402004`
DATABASE_URL = "postgresql://postgres.uitfyfywxzaczubnecft:AMAN%402004@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()



# from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

