import os
import urllib.parse
import uvicorn
from fastapi import FastAPI, Request, Form, Query
from databases import Database
from datetime import datetime


app = FastAPI()
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DATABASE_NAME = 'reddit_goals.db'
TABLE_NAME = 'goals'
DATABASE_LOCATION = os.path.join(CURRENT_DIR_PATH, DATABASE_NAME)
REDDIT_GOALS_DB = Database(f"sqlite:///{DATABASE_LOCATION}")


def humanize_unixtime(unix_time):
    time = datetime.fromtimestamp(int(unix_time)).strftime('%d-%m-%Y %H.%M')
    return time


@app.on_event("startup")
async def database_connect():
    await REDDIT_GOALS_DB.connect()


@app.on_event("shutdown")
async def database_disconnect():
    await REDDIT_GOALS_DB.disconnect()


@app.get("/")
async def fetch_data():
    query = f"SELECT * FROM {TABLE_NAME} ORDER BY created_utc DESC LIMIT 200"
    results = await REDDIT_GOALS_DB.fetch_all(query=query)

    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7777)
