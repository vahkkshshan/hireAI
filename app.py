import shutil
from pathlib import Path
from typing import Optional, List

from bson import ObjectId
from fastapi import FastAPI, Body, HTTPException, status, Form, UploadFile, File, Query, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr
from pymongo import MongoClient

from awsConnector import upload_file_to_bucket
from hashing import Hash
from jwttoken import create_access_token
from model import predict
from oauth import get_current_user

"""creation of FastAPI initiation"""

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

###############################################################################################
"""MongoDB connection initiation"""
client = MongoClient(
    "mongodb+srv://vk26:qwerty123@cluster0.hmntz.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.college

###############################################################################################
""" Creating Pydantic class models for modelling data to be stored inn MongoDB"""


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
    designation: str = Field(...)
    vacancy: int = Field(...)
    company_name: str = Field(...)
    description: str = Field(...)

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


class FacialScore(BaseModel):
    angry: int
    disgust: int
    fear: int
    happy: int
    sad: int
    surprise: int
    neutral: int


class ScoringInfo(BaseModel):
    facial_scores: FacialScore
    final_score: str


class InterviewInfo(BaseModel):
    interview_id: str
    interview_name: str
    company_name: str
    video_link: str
    scores: Optional[ScoringInfo]


class CandidateModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    firstname: str = Field(...)
    lastname: str = Field(...)
    contact_number: str = Field(...)
    username: str = Field(...)
    email: EmailStr = Field(...)
    university: str = Field(...)
    degree_programme: str = Field(...)
    password: str = Field(...)
    cv: Optional[str]
    interview: Optional[List[InterviewInfo]]

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
    firstname: Optional[str]
    lastname: Optional[str]
    contact_number: Optional[str]
    username: Optional[str]
    university: Optional[str]
    degree_programme: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    cv: Optional[str]
    interview: Optional[List[InterviewInfo]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "username": "Jane Doe",
                "firstname": "Jane Doe",
                "lastname": "Jane Doe",
                "university": "Jane Doe",
                "degree_programme": "Jane Doe",
                "contact_number": "Jane Doe",
                "email": "jdoe@example.com",
                "password": "Jane Doe"
            }
        }


"""Below are backend REST API requests that get responses from front end and send back resposes to front end. Also its 
   connected with AWS s3 bucket and mongodb"""


@app.get("/")
def read_root(current_user: UserModel = Depends(get_current_user)):
    return {"data": "Hello OWrld"}


###############################################################################################
"""This API request is used to create admin who would be
   able to access candidate dates and create interviews."""


@app.post('/register', response_description="Add new user", response_model=UserModel)
async def create_user(username: str = Form(None), company: str = Form(None), password: str = Form(None)):
    hashed_pass = Hash.bcrypt(password)
    user = UserModel(username=username, company=company, password=hashed_pass)
    user = jsonable_encoder(user)

    user_id = db["users"].insert_one(user)
    created_user = db["users"].find_one({"_id": user_id.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_user)


###############################################################################################
"""This API is used by Admis and Candidates to login"""


@app.post('/login')
async def login(request: OAuth2PasswordRequestForm = Depends()):
    user = db["users"].find_one({"username": request.username})
    role = "admin"
    if not user:
        user = db["candidate"].find_one({"username": request.username})
        role = "candidate"

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No user found with this {request.username} username')
    if not Hash.verify(user["password"], request.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Wrong Username or password')
    access_token = create_access_token(data={"username": user["username"], "role": role, "id": user["_id"]})
    return {"access_token": access_token, "token_type": "bearer"}


###############################################################################################
"""This API is used by candidates when they are creating a new profile"""


@app.post("/candidate", response_description="Add new candidate", response_model=CandidateModel)
async def create_candidate(username: str = Form(None), email: EmailStr = Form(None),
                           password: str = Form(None), firstname: str = Form(None), lastname: str = Form(None),
                           university: str = Form(None),
                           contact_number: str = Form(None), degree_programme: str = Form(None),
                           cv: UploadFile = File(None),
                           interview_name: str = Query(None, enum=list(db["interview"].find()))):
    hashed_pass = Hash.bcrypt(password)
    candidate = CandidateModel(username=username, email=email, firstname=firstname, lastname=lastname,
                               password=hashed_pass,
                               university=university, contact_number=contact_number, degree_programme=degree_programme,
                               interview=[])
    print(candidate)
    candidate = jsonable_encoder(candidate)
    new_candidate = db["candidate"].insert_one(candidate)
    created_candidate = db["candidate"].find_one({"_id": new_candidate.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_candidate)


###############################################################################################
"""This API is used by Canididates when uploading their CV which is got from 
   Front End to here and then pushed to AWS S3 and the record is saved in MongoDB"""


@app.post("/candidate/cv_upload/{username}", response_description="Upload cv")
async def upload_cv(username: str, cv: UploadFile = File(None)):
    if cv is not None:
        upload_obj = upload_file_to_bucket(cv.file, 'vk26bucket', 'cv', cv.filename)
        if upload_obj:

            candidate = UpdateCandidateModel(cv="https://vk26bucket.s3.ap-south-1.amazonaws.com/cv/" + cv.filename)
            candidate = {k: v for k, v in candidate.dict().items() if v is not None}

            if len(candidate) >= 1:
                update_result = db["candidate"].update_one({"username": username}, {"$set": candidate})

                if update_result.modified_count == 1:
                    if (
                            updated_candidate := db["candidate"].find_one({"username": username})
                    ) is not None:
                        return cv.filename

            if (existing_candidate := db["candidate"].find_one({"username": username})) is not None:
                return cv.filename

            raise HTTPException(status_code=404, detail=f"Candidate {username} not found")


###############################################################################################
"""This API is used when candidate are applying for interviews and hence takes their id, interview id 
   and the interview application videos from front end and its updated in mongoDB adna slo video uploaded to AWS S3"""


@app.post("/interview/apply/{interview_id}/{user_id}", response_description="Apply job",
          response_model=UpdateCandidateModel)
async def apply_interview(interview_id: str, user_id: str, video: UploadFile = File(None)):
    if (add_interview := db["interview"].find_one({"_id": interview_id})) is not None:

        destination = Path("videofile/subject.mp4")

        try:
            with destination.open("wb") as buffer:
                shutil.copyfileobj(video.file, buffer)
        except shutil.Error as err:
            print(err)

        # Predict method is the function that will use the video to generate emotional data from FER library model
        angry, disgust, fear, happy, sad, surprise, neutral = predict(
            "videofile/subject.mp4")

        facial_score = FacialScore(angry=angry, disgust=disgust, sad=sad, fear=fear, surprise=surprise, happy=happy,
                                   neutral=neutral)
        scores = ScoringInfo(facial_scores=facial_score, final_score="hired")

        # upload_file_to_bucket method is the function that will send video to AWS S3
        upload_obj = upload_file_to_bucket(video.file, 'vk26bucket', 'video', video.filename)
        if upload_obj:

            # This InterviewInfo() will initialize the data object which will be uploaded to MongoDB
            interview_info = InterviewInfo(interview_id=add_interview['_id'],
                                           interview_name=add_interview['designation'],
                                           company_name=add_interview['company_name'],
                                           video_link="https://vk26bucket.s3.ap-south-1.amazonaws.com/video/" + video.filename,
                                           scores=scores)

            interview = {k: v for k, v in interview_info.dict().items() if v is not None}
            # Below the interview data model for Candidate table is updated and pushed to mongodb based on candidate ID
            if len(interview) >= 1:

                update_result = db["candidate"].update_one({"_id": user_id},
                                                           {"$push": {"interview": interview}})

                if update_result.modified_count == 1:
                    if (updated_candidate := db["candidate"].find_one({"_id": user_id})) is not None:
                        return updated_candidate

                if (existing_candidate := db["candidate"].find_one({"_id": user_id})) is not None:
                    return existing_candidate

                raise HTTPException(status_code=404, detail=f"Interview {interview_id} and {user_id} not found")
    raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")


###############################################################################################
"""This API is used for creating interviews by admins """


@app.post("/interview", response_description="Add new interview", response_model=InterviewModel)
async def create_interview(designation: str = Form(None), vacancy: int = Form(None), company_name: str = Form(None),
                           description: str = Form(None)):
    # Interview Data Model Object is created for Interview Table
    interview = InterviewModel(designation=designation, vacancy=vacancy, company_name=company_name,
                               description=description)
    interview = jsonable_encoder(interview)
    # The interview is inserted into MongoDB here.
    new_interview = db["interview"].insert_one(interview)
    created_interview = db["interview"].find_one({"_id": new_interview.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_interview)


###############################################################################################
"""This API is used to GET all candiates information from mongoDB and is sent to Front End"""


@app.get(
    "/candidate", response_description="List all candidates", response_model=List[CandidateModel]
)
async def list_candidates():
    candidates = list(db["candidate"].find())
    return candidates


###############################################################################################
"""This API is used to GET all interview information from MongoDB and sent to Front End"""


@app.get(
    "/interview", response_description="List all interview", response_model=List[InterviewModel]
)
async def list_interviews():
    interviews = list(db["interview"].find())
    return interviews


###############################################################################################
"""This API is used to get all applied candidates to a single interview information from mongoDB and sent to Front End"""


@app.get(
    "/candidate/appliedCandidates/{interview_id}", response_description="Get a single candidate",
    response_model=List[CandidateModel]
)
async def show_applied_candidates(interview_id: str):
    if candidates := list(db["candidate"].find({"interview": {"$elemMatch": {"interview_id": interview_id}}})):
        return candidates

    raise HTTPException(status_code=404, detail=f"Candidate {interview_id} not found")


###############################################################################################
"""This API is used to get a single candidate information from mongoDB and sennt to Front End"""


@app.get(
    "/candidate/{id}", response_description="Get a single candidate", response_model=CandidateModel
)
async def show_candidate(id: str):
    if (candidate := db["candidate"].find_one({"_id": id})) is not None:
        return candidate

    raise HTTPException(status_code=404, detail=f"Candidate {id} not found")


###############################################################################################
"""This API is used to get a single interview information from mongoDB and sent to Front End"""


@app.get(
    "/interview/{id}", response_description="Get a single interview", response_model=InterviewModel
)
async def show_interview(id: str):
    if (interview := db["interview"].find_one({"_id": id})) is not None:
        return interview

    raise HTTPException(status_code=404, detail=f"Interview {id} not found")


###############################################################################################
"""This API is used to update a single candidate information in mongoDB"""


@app.put("/candidate/{id}", response_description="Update a candidate", response_model=CandidateModel)
async def update_candidate(id: str, candidate: UpdateCandidateModel = Body(...)):
    candidate = {k: v for k, v in candidate.dict().items() if v is not None}

    if len(candidate) >= 1:
        update_result = db["candidate"].update_one({"_id": id}, {"$set": candidate})

        if update_result.modified_count == 1:
            if (
                    updated_candidate := db["candidate"].find_one({"_id": id})
            ) is not None:
                return updated_candidate

        if (existing_candidate := db["candidate"].find_one({"_id": id})) is not None:
            return existing_candidate

        raise HTTPException(status_code=404, detail=f"Candidate {id} not found")


###############################################################################################
"""This API is used to delete a single candidate information from mongoDB"""


@app.delete("/candidate/{id}", response_description="Delete a candidate")
async def delete_candidate(id: str):
    delete_result = db["candidate"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Cadidate {id} not found")
