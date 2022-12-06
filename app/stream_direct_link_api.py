import os
import urllib.parse
import uvicorn
from fastapi import FastAPI, Request, Form, Query
from fastapi.templating import Jinja2Templates
from stream_direct_link import get_video_source


app = FastAPI()
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATES_PATH = os.path.join(CURRENT_DIR_PATH, 'templates')
templates = Jinja2Templates(directory=TEMPLATES_PATH)


@app.get("/api/{site_name}")
def get_direct_link(site_name=None, id=None):

    stream_dict = {'streamable': 'https://streamable.com/', 'streamja': 'https://streamja.com/',
                   'streamye': 'https://streamye.com/', 'streamvi': 'https://streamvi.com/watch/',
                   'streamwo': 'https://streamwo.com/file/', 'mixture': 'https://mixture.gg/v/',
                   'streamff': 'https://streamff.com/v/', 'clippituser': 'https://clippituser.tv/c/',
                   'streamgg': 'https://streamgg.com/v/', 'fodder': 'https://v.fodder.gg/v/',
                   'streamin': 'https://streamin.me/v/'}

    if site_name in stream_dict:
        url = f'{stream_dict[site_name]}{id}'
        direct_link = get_video_source(url)
        return {"direct_link": direct_link}
    else:
        return {"error": "wrong link"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
