import json
import os
from fastapi import FastAPI, Body, HTTPException, status, Form, UploadFile, File, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr, SecretStr, constr
from bson import ObjectId
from typing import Optional, List, OrderedDict
from pymongo import MongoClient
from awsConnector import upload_file_to_bucket
import motor.motor_asyncio
from hashing import Hash
from jwttoken import create_access_token
from oauth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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


class UserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(...)
    company: str = Field(...)
    password: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "username": "Jane Doe",
                "company": "jdoe@example.com",
                "password": "Software Engineer"
            }
        }


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


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


@app.post("/st", response_description="Add new student", response_model=StudentModel)
async def create_student(student: StudentModel = Body(...)):
    student = jsonable_encoder(student)
    new_student = await db["students"].insert_one(student)
    created_student = await db["students"].find_one({"_id": new_student.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_student)


@app.get("/")
def read_root(current_user: UserModel = Depends(get_current_user)):
    return {"data": "Hello OWrld"}


@app.post('/register', response_description="Add new user", response_model=UserModel)
async def create_user(username: str = Form(None), company: str = Form(None), password: str = Form(None)):
    # print(request.password)
    # print(request)
    # print(request.password)
    hashed_pass = Hash.bcrypt(password)
    # user_object = dict(request)
    user = UserModel(username=username, company=company, password=hashed_pass)
    user = jsonable_encoder(user)
    # print("hi dude")
    # print(user_object["password"])
    # user_object["password"] = hashed_pass
    # print(user_object["password"])

    user_id = await db["users"].insert_one(user)
    created_user = await db["users"].find_one({"_id": user_id.inserted_id})
    # print(user)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


@app.post('/login')
async def login(request: OAuth2PasswordRequestForm = Depends()):
    user = db["users"].find_one({"username": request.username})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No user found with this {request.username} username')
    if not Hash.verify(user["password"], request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Wrong Username or password')
    access_token = create_access_token(data={"username": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/candidate", response_description="Add new candidate", response_model=CandidateModel)
async def create_candidate(name: str = Form(None), email: EmailStr = Form(None), position: str = Form(None),
                           cv: UploadFile = File(...),
                           interview_name: str = Query(None, enum=list(db["interview"].find()))):
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


@app.get(
    "/interview/{id}", response_description="Get a single interview", response_model=InterviewModel
)
async def show_interview(id: str):
    if (interview :=  db["interview"].find_one({"_id": id})) is not None:
        print(interview)
        return interview

    raise HTTPException(status_code=404, detail=f"Interview {id} not found")


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