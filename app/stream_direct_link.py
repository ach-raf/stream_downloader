import configparser
import json
import os
import time
import requests
import uvicorn

from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates


def read_info_file(file_path):
    """function to read informations from info.ini file and return a list of info.

    Args:
        file_path ([str]): [path to read regex from]

    Returns:
        [list]: [list of info]
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    credentials = []
    for section in config.sections():
        for key in config[section]:
            # print(f'{key} = {config[section][key]}')
            credentials.append(config[section][key])
    return credentials


# =================================================================================================
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR_PATH, 'config', 'info.ini')
CONFIG_INFO = read_info_file(CONFIG_PATH)
STREAMJA = CONFIG_INFO[0]
STREAMYE = CONFIG_INFO[1]
STREAMVI = CONFIG_INFO[2]
# =================================================================================================


# =================== SELENIUM CONFIGURATION ===================
PATH_TO_CHROME_DRIVER = os.path.join(
    CURRENT_DIR_PATH, 'chromedriver', 'chromedriver.exe')
# options for selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--incognito")
options.headless = True

CHROME_BROWSER = webdriver.Chrome(
    executable_path=PATH_TO_CHROME_DRIVER, options=options)

# =============================================================


def selenium_soup(_url):
    CHROME_BROWSER.get(_url)
    CHROME_BROWSER.minimize_window()
    # sleep to let the page load
    time.sleep(0.5)
    _html = CHROME_BROWSER.page_source
    return BeautifulSoup(_html, 'html.parser')


def beautiful_soup(_url):
    time.sleep(0.5)
    _html = requests.get(_url).content
    return BeautifulSoup(_html, 'html.parser')


def get_soup(_url):
    if 'streamable' in _url:
        return selenium_soup(_url)
    else:
        return beautiful_soup(_url)


def default_video_source(_url, _soup):
    _site_name = urlparse(_url)
    _site_name = str(_site_name.netloc)[:-4]

    match _site_name:
        case 'streamja':
            _source_css_selector = STREAMJA
        case 'streamye':
            _source_css_selector = STREAMYE
        case 'streamvi':
            _source_css_selector = STREAMVI

    _video_source = None
    try:
        _video_source = _soup.select_one(_source_css_selector)['src']
    except AttributeError:
        print(f'AttributeError {_url}')
        return None
    except TypeError:
        try:
            _soup = selenium_soup(_url)
            _video_source = _soup.select_one(_source_css_selector)['src']
        except TypeError:
            print(f'TypeError {_url}')
    return _video_source


def streamable_direct_link(_soup):
    try:
        _script = _soup.find('script', id='player-js', type='text/javascript')
        for _line in _script:
            if 'var videoObject' in _line:
                for _item in _line.splitlines():
                    if 'var videoObject' in _item:
                        # clean the json object, [:-1] to remove the ;
                        video_object = _item.replace(
                            'var videoObject = ', '').strip()[:-1]
                        # parse the json object
                        video_object = json.loads(video_object)
                        return video_object['files']['mp4']['url'].replace('//', 'https://')
    except TypeError:
        return None


def get_video_source(_url):
    _soup = get_soup(_url)
    if 'streamable' in _url:
        return streamable_direct_link(_soup)
    else:
        if default_video_source(_url, _soup):
            return default_video_source(_url, _soup)
        else:
            return None


app = FastAPI()
TEMPLATES_PATH = os.path.join(CURRENT_DIR_PATH, 'templates')
templates = Jinja2Templates(directory=TEMPLATES_PATH)


@app.get("/")
def form_post(request: Request):
    result = "Type a url"
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})


@app.post("/")
def form_post(request: Request, url: str = Form(...)):
    result = get_video_source(url)
    print(result)
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0")
