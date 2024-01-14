from os import environ
from sys import stderr
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from typing import Final
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

MONGO_DB_URI: Final[str] = environ['DUMP_DB_URI']

client: MongoClient = MongoClient(MONGO_DB_URI, server_api=ServerApi('1'))
app = FastAPI()

try:
    client.admin.command('ping')
    print('Successfully connected to MongoDB.')
except Exception as e:
    print(f'Couldn\'t connect to the database: {e}', file=stderr)


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


@app.get('/jobs/capitals/{city}')
async def get_capital_city_jobs(city: str):
    pass


@app.get('/jobs/capitals/{keyword}')
async def get_capital_keyword_jobs(keyword: str):
    pass


@app.get('/jobs/capitals/{keyword}/{city}')
async def get_capital_city_keyword_jobs(keyword: str, city: str):
    pass
