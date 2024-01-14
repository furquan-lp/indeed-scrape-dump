from os import environ
from sys import stderr
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Final
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.database import Database
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

load_dotenv()

MONGO_DB_URI: Final[str] = environ['DUMP_DB_URI']
MONGO_DB_NAME: Final[str] = environ['DUMP_DB_NAME']

keywords: list[str] = environ['DUMP_DB_VALID_KEYWORDS'].split(', ')
client: MongoClient = MongoClient(MONGO_DB_URI, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print('Successfully connected to MongoDB.')
except Exception as e:
    print(f'Couldn\'t connect to the database: {e}', file=stderr)

db: Database = client[MONGO_DB_NAME]

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title='Indeed Dump API',
              summary='An API to access the January 2024 100k job dump scraped from Indeed',
              version='0.6.0')
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore
app.add_middleware(SlowAPIMiddleware)


@app.get('/')
async def root() -> HTMLResponse:
    index_html: str = ''
    try:
        with open('index.html', encoding='utf-8') as f:
            index_html = f.read()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return HTMLResponse(content=index_html)


@app.get('/jobs/capitals/city/{city}')
async def get_capital_city_jobs(city: str):
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Not implemented yet")


@app.get('/jobs/capitals/{keyword}')
@limiter.limit("5/minute")
async def get_capital_keyword_jobs(keyword: str, request: Request):
    if keyword not in keywords:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f'Keyword \'{keyword}\' not valid for the database')
    else:
        collection = db[keyword]
        if collection.count_documents({}) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No jobs found for \'{keyword}\'')
        found_items: list[dict] = [{'city': i.get('city', ''), 'state': i.get(
            'state', ''), 'jobs': i.get('jobs', {})} for i in collection.find()]
        return {keyword: found_items}


@app.get('/jobs/capitals/{keyword}/{city}')
async def get_capital_city_keyword_jobs(keyword: str, city: str):
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Not implemented yet")


@app.get('/keywords')
async def get_valid_keywords():
    return {'valid_keywords': keywords}
