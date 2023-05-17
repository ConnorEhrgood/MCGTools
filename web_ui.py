import os
from time import sleep
from MCGTools import kicopy, ptcopy
from ast import Str
from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
from fastapi.responses import RedirectResponse
import bson
from bson import ObjectId
from bson.json_util import dumps, loads
import json


server_address = os.environ.get('SERVER_ADDRESS')
print(server_address)

api = FastAPI()

origins = [ #Allowable origins for CORS
    server_address
]

api.add_middleware( #CORS setup to make sure it can be run from the main web server
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient(os.environ.get('DB_CONNECT_STRING'))
db = client[os.environ.get('DB_NAME')]

def json_person(person) -> dict:

    json_person = {}

    for field in person.keys():
        if person[field]:
            if field == '_id':
                json_person["person_id"] = str(person['_id'])
            elif field == 'date_birth' or field == 'date_death':
                json_person[field] = person[field].strftime("%-m/%-d/%Y")
            else:
                json_person[field] = person[field]

    return json_person


def json_transfer(transfer) -> dict:

    json_transfer = {}

    for field in transfer.keys():
        if transfer[field]:
            if field == '_id':
                json_transfer["transfer_id"] = str(transfer['_id'])
            elif field == 'init_time':
                json_transfer[field] = transfer[field].strftime("%-m/%-d/%Y, %-H:%M:%S")
            elif field == 'files' or field == 'errors':
                json_transfer[field] = []
                for i, file in enumerate(transfer[field]):
                    json_transfer[field].append(file)  # add empty dict for each file/error
                    json_transfer[field][i]['time'] = transfer[field][i]['time'].strftime("%-m/%-d/%Y, %-H:%M:%S")
            else:
                json_transfer[field] = transfer[field]

    return json_transfer


@api.get("/")
async def root(): #This function returns a message with the API version.
    return {"message": "MAP Ingest API Version 0.1"}

@api.post('/kicopy/')
async def kicopy_xfer(name: str = Form(), config: str = Form()): #This is the function that handles a KiCopy Transfer
    t = Thread(target=kicopy, args=(name, config, )) #Defining KiCopy thread
    t.start() #Start PTCopy
    sleep(0.25) #Wait to make sure the DB entries are in before user is redirected
    return RedirectResponse(f'{server_address}/transfers/') #Redirect user to transfers page

@api.post('/ptcopy/')
async def ptcopy_xfer(name: str = Form(), config: str = Form()): #This is the function that handles a PTCopy Transfer
    t = Thread(target=ptcopy, args=(name, config, )) #Defining PTCopy thread
    t.start() #Start PTCopy
    sleep(0.25) #Wait to make sure the DB entries are in before user is redirected
    return RedirectResponse(f'{server_address}/transfers/') #Redirect user to transfers page

@api.post('/show_copy/')
async def show_xfer(name: str = Form(), config: str = Form()): #This is the function that handles a full show transfer
    kt = Thread(target=kicopy, args=(name, config, )) #Defining KiCopy thread
    kt.start() #Start KiCopy
    pt = Thread(target=ptcopy, args=(name, config, )) #Defining PTCopy thread
    pt.start() #Start PTCopy
    sleep(0.25) #Wait to make sure the DB entries are in before user is redirected
    return RedirectResponse(f'{server_address}/transfers/') #Redirect user to transfers page

@api.get('/transfers/')
async def get_transfers(): #This function returns the database entries for the 10 most recent transfers

    #Mongo Aggregation
    transfers_ls = list(db['transfers'].aggregate([
        {
            '$sort': {
                'init_time': -1
            }
        }, {
            '$limit': 10
        }, {
            '$addFields': {
                'transfer_id': {
                    '$convert': {
                        'input': '$_id', 
                        'to': 'string'
                    }
                }
            }
        }, {
            '$project': {
                '_id': 0,
                'config' : 0
            }
        }
    ]))
    for transfer in transfers_ls:
        transfer['init_time'] = transfer['init_time'].strftime("%-m/%-d/%Y, %-H:%M:%S")

    return transfers_ls #That's all! Mongo does most of the heavy lifting here.

@api.post('/add_person/')
async def add_person(
    name_prefix: str = Form(None), name_first: str = Form(), name_nickname: str = Form(None),
    name_middle: str = Form(None), name_last: str = Form(), name_suffix: str = Form(None),
    date_birth: str = Form(None), date_death: str = Form(None), desc_brief: str = Form(),
    desc_full: str = Form(None)
    ):

    from datetime import datetime

    fields = [
        'name_prefix', 'name_first', 'name_nickname',
        'name_middle', 'name_last', 'name_suffix',
        'date_birth', 'date_death', 'desc_brief', 'desc_full'
        ]

    person = {}

    for field in fields:
        if locals()[field]:
            if field == 'date_birth' or field == 'date_death':
                person[field] = datetime.strptime(locals()[field], '%Y-%m-%d')
            else:
                person[field] = locals()[field]

    entry = db.people.insert_one(person).inserted_id
    return RedirectResponse(f'{server_address}/person?person_id={entry}')

@api.get('/person')
def get_person(person_id: str):

    try:
        person_id = ObjectId(person_id)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId. ObjectId must be a 24-character hex string")
    
    person = db.people_import_stage3.find_one({"_id": person_id})
    person_json = json_person(person)

    return person_json

@api.get("/people")
def get_people(search_text: str = None):

    if search_text:
        people = list(db.people_import_stage3.aggregate([
            {
                '$search': {
                    'index': 'default', 
                    'text': {
                        'query': search_text, 
                        'path': [
                            'name_first', 'name_nickname', 'name_middle', 
                            'name_last', 'name_prefix', 'name_suffix',
                            'desc_brief', 'desc_full', 'role'
                        ],
                        'fuzzy': {}
                    }
                }
            }, {
                '$project': {
                    'id': { '$toString': '$_id' }, 
                    '_id': 0, 'name_first': 1, 'name_nickname': 1, 
                    'name_last': 1, 'name_suffix': 1, 'desc_brief': 1, 
                    'role': 1, 'appearances': 1
                }
            }
        ]))


    else:
        # Retrieve all documents in the "people" collection
        people = list(db.people_import_stage3.find({},{ '_id': 1, 'name_first': 1, 'name_nickname': 1, 'name_last': 1, 'name_suffix': 1, 'desc_brief': 1, 'role': 1, 'appearances': 1}))
        for person in people:
            person["id"] = str(person.pop("_id"))
    return people

@api.get('/transfer')
def get_person(transfer_id: str):

    try:
        transfer_id = ObjectId(transfer_id)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId. ObjectId must be a 24-character hex string")
    
    transfer = db.transfers.find_one({"_id": transfer_id})
    transfer_json = json_transfer(transfer)

    return transfer_json
