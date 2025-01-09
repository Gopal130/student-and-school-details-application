from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Database URL for PostgreSQL
URL_DATABASE = 'postgresql://myuser:password@localhost:5432/student_school'

# Setup SQLAlchemy engine and sessionmaker
engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
