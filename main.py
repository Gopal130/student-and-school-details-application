from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Annotated
import models
from database import engine, SessionLocal
from sqlalchemy.exc import SQLAlchemyError

from models import School, Student

app = FastAPI()

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

class SchoolBase(BaseModel):
    school_name: str
    school_code: str  

class SchoolResponse(BaseModel):
    school_name: str
    school_code: str

    class Config:
        orm_mode = True

class StudentBase(BaseModel):
    year:int
    name: str
    class_name: str
    section: str
    city: str
    school_code:str


class StudentResponse(BaseModel):
    year:int
    roll_number: str
    name: str
    class_name: str
    section: str
    city: str
    school_code:str

    class Config:
        orm_mode = True

class UpdateStudent(BaseModel):
    name: str = None  # optional
    section: str = None  # optional
    class_name: str = None  # optional

    class Config:
        orm_mode = True
class Updateschool(BaseModel):
    school_name:str=None
    school_code:str=None

    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/schools/", response_model=SchoolResponse)
async def create_school(school: SchoolBase, db: Session = Depends(get_db)):
    try:
        # Check if the school already exists by name or code
        existing_school = db.query(School).filter(School.school_name == school.school_name).first()
        if existing_school:
            raise HTTPException(status_code=400, detail=f"School with name '{school.school_name}' already exists.")
        
        existing_code = db.query(School).filter(School.school_code == school.school_code).first()
        if existing_code:
            raise HTTPException(status_code=400, detail=f"School with school code '{school.school_code}' already exists.")
        
        # Create the new school
        db_school = School(
            school_name=school.school_name,
            school_code=school.school_code
        )
        
        db.add(db_school)
        db.commit()
        db.refresh(db_school)

        return db_school
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@app.post("/students/", response_model=StudentResponse)
async def create_student(student: StudentBase, db: Session = Depends(get_db)):
    try:
        # Check if the school exists by school_code
        school = db.query(School).filter(School.school_code == student.school_code).first()
        if not school:
            raise HTTPException(status_code=404, detail=f"School with code '{student.school_code}' not found")
        
        # Find the latest roll number for this school and year
        latest_student = db.query(Student).filter(Student.school_code == student.school_code, Student.year == student.year).order_by(Student.roll_number.desc()).first()
        
        # Extract the 4-digit number from the last roll number if any
        if latest_student:
            # The roll number format is 'school_code<year>xxxx', so we extract the last 4 digits
            last_roll_number = latest_student.roll_number
            last_number = int(last_roll_number[-4:]) if last_roll_number[-4:].isdigit() else 0
            new_number = last_number + 1
        else:
            new_number = 1
        
        # Ensure the new 4-digit number is in the correct format
        new_roll_number = f"{student.school_code}{student.year}{new_number:04d}"
        
        # Create the new student
        db_student = Student(
            roll_number=new_roll_number,
            name=student.name,
            class_name=student.class_name,
            section=student.section,
            city=student.city,
            school_code=student.school_code,  # school_code is used now instead of school_id
            year=student.year
        )
        
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        
        return db_student
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/students", response_model=List[StudentBase])  # Use the Pydantic model here
async def get_students(db: Session = Depends(get_db)):
    try:
        # Query the database to get all students
        students = db.query(models.Student).all()

        # If no students are found, raise an error
        if not students:
            raise HTTPException(status_code=404, detail="No students found")

        return students

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")
    
@app.get("/schools", response_model=List[SchoolBase])  # Using Pydantic model here
async def get_schools(db: Session = Depends(get_db)):
    try:
        # Query the database to get all schools
        schools = db.query(models.School).all()

        # If no schools are found, raise an error
        if not schools:
            raise HTTPException(status_code=404, detail="No schools found")

        return schools

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")

@app.delete("/students/school/{Roll_number}", response_model=dict)
async def delete_student_by_roll_number(Roll_number: str, db: Session = Depends(get_db)):
    try:
        # Find all students by school_id
        db_students = db.query(models.Student).filter(models.Student.roll_number == Roll_number).first()

        # If no students found, raise an error
        if not db_students:
            raise HTTPException(status_code=404, detail=f"No students found with roll number {Roll_number}")

        # Delete all students associated with the school
        db.delete(db_students)

        db.commit()

        return {"messsection": f"Student with roll number {Roll_number} deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()  # Rollback transaction in case of any database error
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    except Exception as e:
        db.rollback()  # Rollback in case of unexpected error
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")


@app.delete("/schools/{school_code}", response_model=dict)
async def delete_school_by_school_id(school_code: str, db: Session = Depends(get_db)):
    try:
        # Find the school by id (the correct column name in the model)
        db_school = db.query(models.School).filter(models.School.school_code == school_code).first()

        # If no school is found, raise an error
        if not db_school:
            raise HTTPException(status_code=404, detail=f"No school found with school_code {school_code}")

        # Delete the school record
        db.delete(db_school)

        # Commit the transaction to apply the changes
        db.commit()

        return {"message": f"School with School code {school_code} deleted successfully"}

    except SQLAlchemyError as e:
        db.rollback()  # Rollback transaction in case of any database error
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    except Exception as e:
        db.rollback()  # Rollback in case of unexpected error
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")

@app.put("/students/{Roll_number}", response_model=dict)
async def update_student_details(Roll_number: str, update_data: UpdateStudent, db: Session = Depends(get_db)):
    try:
        # Fetch the student by roll number
        db_student = db.query(models.Student).filter(models.Student.roll_number == Roll_number).first()

        # If the student is not found, raise an error
        if not db_student:
            raise HTTPException(status_code=404, detail=f"No student found with roll number {Roll_number}")

        # Update the student's details if provided
        if update_data.name:
            db_student.name = update_data.name
        if update_data.section:
            db_student.section = update_data.section
        if update_data.class_name:
            db_student.class_name = update_data.class_name

        # Commit the changes to the database
        db.commit()

        # Return a success messsection with the updated student details
        return {
            "messsection": f"Student with roll number {Roll_number} updated successfully",
            "student": {
                "roll_number": db_student.roll_number,
                "name": db_student.name,
                "section": db_student.section,
                "class_name": db_student.class_name
            }
        }

    except SQLAlchemyError as e:
        db.rollback()  # Rollback transaction in case of any database error
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    except Exception as e:
        db.rollback()  # Rollback in case of unexpected error
        raise HTTPException(status_code=500, detail=f"Unexpected error occurred: {str(e)}")


@app.put("/schools/{school_code}", response_model=dict)
async def update_school_details(school_code: str, update: Updateschool, db: Session = Depends(get_db)):
    try:
        # Fetch the school by its current school_code
        db_school = db.query(models.School).filter(models.School.school_code == school_code).first()

        # If the school is not found, raise an error
        if not db_school:
            raise HTTPException(status_code=404, detail=f"No school found with school code {school_code}")

        # Check if the school name already exists (excluding the current school)
        if update.school_name:
            existing_school = db.query(models.School).filter(models.School.school_name == update.school_name).first()
            if existing_school and existing_school.school_code != school_code:
                raise HTTPException(status_code=400, detail=f"School name '{update.school_name}' already exists.")

        # Update school details
        if update.school_name:
            db_school.school_name = update.school_name

        # Update the school code only if it's different
        if update.school_code and update.school_code != school_code:
            new_school_code = update.school_code
            old_school_code = db_school.school_code

            # Validate that the new school code doesn't already exist
            existing_school_code = db.query(models.School).filter(models.School.school_code == new_school_code).first()
            if existing_school_code:
                raise HTTPException(status_code=400, detail=f"School code '{new_school_code}' already exists.")

            # Update the school code in the school table
            db_school.school_code = new_school_code

            # Fetch all students associated with the old school_code
            students = db.query(models.Student).filter(models.Student.school_code == old_school_code).all()

            # Update the school_code and roll_number for all students linked to the old school_code
            for student in students:
                student.school_code = new_school_code  # Update the school_code reference for the student
                student.roll_number = generate_new_roll_number(student, new_school_code, db)  # Update the roll_number

            # Commit the changes to both the school and student tables
            db.commit()

            # Refresh the session to ensure changes are applied
            db.refresh(db_school)

        # Commit changes to the school details (if any)
        db.commit()

        return {"message": f"School with code {school_code} and associated students updated successfully"}

    except Exception as e:
        db.rollback()  # Rollback in case of any error
        raise HTTPException(status_code=500, detail=str(e))


# Helper function to generate the new roll number based on school_code, year, and new number
def generate_new_roll_number(student, new_school_code: str, db: Session) -> str:
    # Generate roll number like: "{school_code}{year}{new_number:04d}"
    new_number = get_next_roll_number(student, new_school_code, db)  # Pass the db session here
    return f"{new_school_code}{student.year}{new_number:04d}"


# Function to fetch the next available roll number for a student
def get_next_roll_number(student, new_school_code: str, db: Session) -> int:
    # Get the highest roll number from students of the same school_code
    max_roll_number = db.query(models.Student).filter(models.Student.school_code == new_school_code).order_by(models.Student.roll_number.desc()).first()

    # If there is a student with an existing roll number, get the next one
    if max_roll_number:
        # Extract the last 4 digits from the existing roll number
        current_number_str = max_roll_number.roll_number[len(new_school_code) + len(str(student.year)):]  # Skip the school code and year parts
        current_number = int(current_number_str)  # Convert it to an integer
        return current_number + 1
    else:
        return 1  # If no existing roll numbers, start from 1

