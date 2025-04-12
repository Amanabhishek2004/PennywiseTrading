from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import sessionmaker   
# Database URL
DATABASE_URL = "postgresql://postgres:Aman2004@localhost:5432/Pennywise"
# Create the SQLAlchemy engine 
engine = create_engine(DATABASE_URL)
 # Base class for defining models
Base = declarative_base() # SessionLocal will be used for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)  # Dependency for getting the database session 
def get_db():    
  db = SessionLocal()     
  try:       
     yield db     
  finally:    
      db.close()  # Create tables for all models that inherit from Base def create_database():     print("Creating tables...")     Base.metadata.create_all(bind=engine)     print("Tables created successfully!") 
