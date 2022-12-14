import os
from time import sleep
from MCGTools import kicopy, ptcopy
from ast import Str
from fastapi import FastAPI, Form
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
from fastapi.responses import RedirectResponse


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

@api.get("/")
async def root(): #This function returns a message with the API version.
    return {"message": "MAP Ingest API Version 0.1"}

@api.post('/kicopy/')
async def kicopy_xfer(name: str = Form(''), config: str = Form('')): #This is the function that handles a KiCopy Transfer
    t = Thread(target=kicopy, args=(name, config, )) #Defining KiCopy thread
    t.start() #Start PTCopy
    sleep(0.25) #Wait to make sure the DB entries are in before user is redirected
    return RedirectResponse(f'{server_address}/transfers/') #Redirect user to transfers page

@api.post('/ptcopy/')
async def ptcopy_xfer(name: str = Form(''), config: str = Form('')): #This is the function that handles a PTCopy Transfer
    t = Thread(target=ptcopy, args=(name, config, )) #Defining PTCopy thread
    t.start() #Start PTCopy
    sleep(0.25) #Wait to make sure the DB entries are in before user is redirected
    return RedirectResponse(f'{server_address}/transfers/') #Redirect user to transfers page

@api.post('/show_copy/')
async def show_xfer(name: str = Form(''), config: str = Form('')): #This is the function that handles a full show transfer
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

    return transfers_ls #That's all! Mongo does most of the heavy lifting here.

