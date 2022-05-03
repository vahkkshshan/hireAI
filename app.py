import json
import os
from fastapi import FastAPI, Body, HTTPException, status, Form, UploadFile, File,Query
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr, SecretStr, constr
from bson import ObjectId
from typing import Optional, List,OrderedDict
from pymongo import MongoClient
from awsConnector import upload_file_to_bucket
import motor.motor_asyncio

app = FastAPI()
# client = MongoClient()
# client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
# db = client.college
# export MONGODB_URL="mongodb+srv://vk26:qwerty123@testcluster.hmntz.mongodb.net/college?retryWrites=true&w=majority"


client = MongoClient(
    "mongodb+srv://vk26:qwerty123@cluster0.hmntz.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.college


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class StudentModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    email: EmailStr = Field(...)
    course: str = Field(...)
    gpa: float = Field(..., le=4.0)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }


class InterviewModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    vacancy: int = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "position": "Software Engineer",
                "cv": "doe.pdf",
            }
        }


class InterviewInfo(BaseModel):
    interview_id: PyObjectId
    interview_name: str


class CandidateModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    email: EmailStr = Field(...)
    position: str = Field(...)
    cv: str = Field(...)
    interview: List[InterviewInfo]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "position": "Software Engineer",
                "cv": "doe.pdf",
            }
        }


class UpdateCandidateModel(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    position: Optional[str]
    cv: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }


class UpdateStudentModel(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    course: Optional[str]
    gpa: Optional[float]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "Jane Doe",
                "email": "jdoe@example.com",
                "course": "Experiments, Science, and Fashion in Nanophotonics",
                "gpa": "3.0",
            }
        }


# @app.post("/", response_description="Add new student", response_model=StudentModel)
# async def create_student(student: StudentModel = Body(...)):
#     student = jsonable_encoder(student)
#     new_student = await db["students"].insert_one(student)
#     created_student = await db["students"].find_one({"_id": new_student.inserted_id})
#     return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_student)


@app.post("/candidate", response_description="Add new candidate", response_model=CandidateModel)
async def create_candidate(name: str = Form(None), email: EmailStr = Form(None), position: str = Form(None),
                           cv: UploadFile = File(...), interview_name: str = Query(None, enum=list(db["interview"].find()))):
    print("hey")
    ins = list(db["interview"].find())
    print(ins)
    print(interview_name[1])

    # upload_obj = upload_file_to_bucket(cv.file, 'vk26bucket', 'cv', cv.filename)
    # if upload_obj:
    #     query = {"name": interview_name}
    #     add_interview = db["interview"].find_one(query)
    #     print(add_interview["name"])
    #     # for doc in add_interview:
    #     #     print(doc)
    #     if add_interview['vacancy'] is not 0:
    #         interview_info = InterviewInfo(interview_id=add_interview['_id'], interview_name=add_interview['name'])
    #         candidate = CandidateModel(name=name, email=email, position=position,
    #                                    cv="https://vk26bucket.s3.ap-south-1.amazonaws.com/cv" + cv.filename,
    #                                    interview=[interview_info])
    #         print(candidate)
    #         candidate = jsonable_encoder(candidate)
    #         new_candidate = await db["candidate"].insert_one(candidate)
    #         created_candidate = await db["candidate"].find_one({"_id": new_candidate.inserted_id})
        #     return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_candidate)


@app.post("/interview", response_description="Add new interview", response_model=InterviewModel)
async def create_interview(name: str = Form(None), vacancy: int = Form(None)):
    print("hey")
    interview = InterviewModel(name=name, vacancy=vacancy)
    print(interview)
    interview = jsonable_encoder(interview)
    new_interview = await db["interview"].insert_one(interview)
    created_interview = await db["interview"].find_one({"_id": new_interview.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_interview)


@app.get(
    "/candidate", response_description="List all candidates", response_model=List[CandidateModel]
)
async def list_candidates():
    candidates = await db["candidates"].find().to_list(1000)
    return candidates


@app.get(
    "/candidate/{id}", response_description="Get a single candidate", response_model=CandidateModel
)
async def show_candidate(id: str):
    if (candidate := await db["candidate"].find_one({"_id": id})) is not None:
        return candidate

    raise HTTPException(status_code=404, detail=f"Candidate {id} not found")


@app.put("/candidate/{id}", response_description="Update a candidate", response_model=CandidateModel)
async def update_candidate(id: str, candidate: UpdateCandidateModel = Body(...)):
    candidate = {k: v for k, v in candidate.dict().items() if v is not None}

    if len(candidate) >= 1:
        update_result = await db["candidate"].update_one({"_id": id}, {"$set": candidate})

        if update_result.modified_count == 1:
            if (
                    updated_candidate := await db["candidate"].find_one({"_id": id})
            ) is not None:
                return updated_candidate

    if (existing_candidate := await db["candidate"].find_one({"_id": id})) is not None:
        return existing_candidate

    raise HTTPException(status_code=404, detail=f"Candidate {id} not found")


@app.delete("/candidate/{id}", response_description="Delete a candidate")
async def delete_candidate(id: str):
    delete_result = await db["candidate"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Cadidate {id} not found")


















# @app.get(
#     "/", response_description="List all students", response_model=List[StudentModel]
# )
# async def list_students():
#     students = await db["students"].find().to_list(1000)
#     return students























# @app.get(
#     "/{id}", response_description="Get a single student", response_model=StudentModel
# )
# async def show_student(id: str):
#     if (student := await db["students"].find_one({"_id": id})) is not None:
#         return student
#
#     raise HTTPException(status_code=404, detail=f"Student {id} not found")
#
#
# @app.put("/{id}", response_description="Update a student", response_model=StudentModel)
# async def update_student(id: str, student: UpdateStudentModel = Body(...)):
#     student = {k: v for k, v in student.dict().items() if v is not None}
#
#     if len(student) >= 1:
#         update_result = await db["students"].update_one({"_id": id}, {"$set": student})
#
#         if update_result.modified_count == 1:
#             if (
#                     updated_student := await db["students"].find_one({"_id": id})
#             ) is not None:
#                 return updated_student
#
#     if (existing_student := await db["students"].find_one({"_id": id})) is not None:
#         return existing_student
#
#     raise HTTPException(status_code=404, detail=f"Student {id} not found")
#
#
# @app.delete("/{id}", response_description="Delete a student")
# async def delete_student(id: str):
#     delete_result = await db["students"].delete_one({"_id": id})
#
#     if delete_result.deleted_count == 1:
#         return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)
#
#     raise HTTPException(status_code=404, detail=f"Student {id} not found")
