import os
from fastapi import FastAPI,HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel,Field
from supabase import create_client, Client
load_dotenv()



app = FastAPI()
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
client = create_client(SUPABASE_URL,SUPABASE_KEY)

response = client.table("courses").select("*").execute()

class Course(BaseModel):
    course_id:int
    course_name:str = Field(min_length=4, max_length=100)
    description:str

@app.post("/courses")
def create_course(course: Course):
    response =client.table('courses').insert(course.dict()).execute()
    return response.data

@app.get("/courses")
def get_courses():
    response = client.table('courses').select("*").execute()
    return response.data

@app.get("/students/{studentId}/courses")
def get_student_courses(studentId):
    response = client.table("students").select("""
        student_id,
        student_name,
        student_enrollments (
            enrolled_date,
            courses (
                course_id,
                course_name,
                description
            )
        )
    """).eq("student_id", studentId).execute()

    return response.data
               
class Enrollment(BaseModel):
    student_id:int = Field(gt=0)
    course_id:int = Field(gt=0)

@app.post("/enroll")
def enroll_student_in_course(enrollment: Enrollment):
    student = client.table("students").select("student_id").eq("student_id", enrollment.student_id).execute()
    course = client.table("courses").select("course_id").eq("course_id",enrollment.course_id).execute()

    if not student.data:
     raise HTTPException(
        status_code=404,
        detail="Student not found"
     )

    if not course.data:
        raise HTTPException(
            status_code=404,
            detail="Course not found"
        )

    enrolled = client.table('student_enrollments').select("enrollment_id")\
    .eq("student_id", enrollment.student_id).eq("course_id", enrollment.course_id).execute()

    if enrolled.data:
        raise HTTPException(
            status_code=409,
            detail="Student already enrolled in the course"
        )
    
    response =client.table('student_enrollments').insert(enrollment.dict()).execute()
    return response.data

@app.delete("/enroll/{enrollment_id}")
def course_completed(enrollment_id):
    response = client.table("student_enrollments").delete().eq("enrollment_id",enrollment_id).execute()

    if response.data:
        return "successfully deleted enrollment for the student"
    else:
        raise HTTPException(
                status_code=404,
                detail="enrollment not found"
        )
        
   




