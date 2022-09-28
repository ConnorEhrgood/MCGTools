from MCGTools import kicopy
from ast import Str
from fastapi import FastAPI, Form
from pydantic import BaseModel

api = FastAPI()


@api.get("/")
async def root():
    return {"message": "Hello World"}

@api.post("/kicopy/")
async def kicopy_xfer(name: str = Form(), config: str = Form()):
    kicopy(name,config)
    return {"name": name, "config": config}