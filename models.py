from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class School(Base):
    __tablename__ = 'schools'

    school_code = Column(String, primary_key=True, index=True, unique=True)
    school_name = Column(String, index=True, unique=True)

    # Define the relationship with students
    students = relationship('Student', back_populates='school', cascade="all, delete")

class Student(Base):
    __tablename__ = 'students'

    roll_number = Column(String, primary_key=True, index=True)
    name = Column(String)
    class_name = Column(String)
    section = Column(String)
    city = Column(String)
    year=Column(Integer)
    school_code = Column(String, ForeignKey("schools.school_code"))

    # Define the relationship back to the School model
    school = relationship("School", back_populates="students",cascade="all, delete")