import os
import re
import urllib.parse
import uvicorn
from fastapi import FastAPI, Request, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from stream_direct_link import get_video_source
from reddit_downloader import reddit_downloader


##########################################################################################
app = FastAPI()
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATES_PATH = os.path.join(CURRENT_DIR_PATH, 'templates')
templates = Jinja2Templates(directory=TEMPLATES_PATH)
LOCAL_HOST = '127.0.0.1'
HOST = '0.0.0.0'
##########################################################################################


@app.get("/")
def form_post(request: Request):
    result = "Type a url"
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})


@app.post("/")
def form_post(request: Request, url: str = Form(...)):
    if 'reddit' in url or 'redd.it' in url:
        file_path = reddit_downloader(url)
        base_path, filename = os.path.split(file_path)
        return FileResponse(path=file_path, filename=filename, media_type='text/mp4')
    else:
        result = get_video_source(url)
        print(result)
        return templates.TemplateResponse('form.html', context={'request': request, 'result': result})


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=8000)
