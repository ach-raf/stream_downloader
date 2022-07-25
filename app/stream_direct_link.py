import configparser
import json
import os
import time
import requests


from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def read_info_file(file_path):
    """function to read informations from info.ini file and return a list of info.

    Args:
        file_path ([str]): [path to read regex from]

    Returns:
        [list]: [list of info]
    """
    config = configparser.ConfigParser()
    config.read(file_path)
    credentials = {}
    for section in config.sections():
        temp_creds_dict = {}
        for key in config[section]:
            #print(f'{key} = {config[section][key]}')
            temp_creds_dict[key] = config[section][key]
        credentials[section] = temp_creds_dict
    return credentials


# =================================================================================================
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(CURRENT_DIR_PATH, 'config', 'info.ini')
CONFIG_INFO = read_info_file(CONFIG_PATH)
CONFIG_INFO = CONFIG_INFO['STREAM_REGEX']

# =================================================================================================
# =================== SELENIUM CONFIGURATION ===================
PATH_TO_CHROME_DRIVER = os.path.join(
    CURRENT_DIR_PATH, 'chromedriver', 'chromedriver')
# options for selenium
# CHROME_OPTIONS for selenium
CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument('--headless')
CHROME_OPTIONS.add_argument("--incognito")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-crash-reporter")
CHROME_OPTIONS.add_argument("--disable-extensions")
CHROME_OPTIONS.add_argument("--disable-in-process-stack-traces")
CHROME_OPTIONS.add_argument("--disable-logging")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")
CHROME_OPTIONS.add_argument("--log-level=3")
CHROME_OPTIONS.add_argument("--output=/dev/null")
CHROME_OPTIONS.add_argument("--disable-gpu")
CHROME_OPTIONS.add_argument("--disable-features=NetworkService")
CHROME_OPTIONS.add_argument("--window-size=1280x720")
CHROME_OPTIONS.add_argument("--disable-features=VizDisplayCompositor")
CHROME_OPTIONS.add_argument("--enable-features=NetworkService")
CHROME_OPTIONS.add_argument("--NetworkServiceInProcess")

#chrome_options.headless = True

SELENIUM_SERVICE = Service(PATH_TO_CHROME_DRIVER)


# =============================================================


def selenium_soup(_url):
    CHROME_BROWSER = webdriver.Chrome(
        options=CHROME_OPTIONS, service=SELENIUM_SERVICE)

    CHROME_BROWSER.get(_url)
    # sleep to let the page load
    time.sleep(0.5)
    _html = CHROME_BROWSER.page_source
    CHROME_BROWSER.close()
    CHROME_BROWSER.quit()
    return BeautifulSoup(_html, 'html.parser')


def beautiful_soup(_url):
    time.sleep(0.1)
    _html = requests.get(_url).content
    return BeautifulSoup(_html, 'html.parser')


def get_soup(_url):
    if 'streamable' in _url:
        return selenium_soup(_url)
    else:
        return beautiful_soup(_url)


def default_video_source(_url, _soup):
    _site_name = urlparse(_url)

    if 'www' not in str(_site_name.netloc):
        _site_name = str(_site_name.netloc).split('.')[0]
    else:
        _site_name = str(_site_name.netloc).split('.')[1]

    match _site_name:
        case 'streamja':
            _source_css_selector = CONFIG_INFO['streamja']
        case 'streamye':
            _source_css_selector = CONFIG_INFO['streamye']
        case 'streamvi':
            _source_css_selector = CONFIG_INFO['streamvi']
        case 'streamwo':
            _source_css_selector = CONFIG_INFO['streamwo']
        case 'mixture':
            _source_css_selector = CONFIG_INFO['mixture']
        case 'streamff':
            _source_css_selector = CONFIG_INFO['streamff']
        case 'clippituser':
            _source_css_selector = CONFIG_INFO['clippituser']
        case 'streamgg':
            _source_css_selector = CONFIG_INFO['streamgg']
        case 'fodder':
            _source_css_selector = CONFIG_INFO['fodder']
        case _:
            return None

    _video_source = None
    try:
        _video_source = _soup.select_one(_source_css_selector)['src']
        print('_video_source', _video_source)
    except AttributeError:
        print(f'AttributeError {_url}')
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
    _site_name = urlparse(_url)
    _site_name = str(_site_name.netloc).split('.')[0]
    match _site_name:
        case 'streamable':
            return streamable_direct_link(_soup)
        case _:
            return default_video_source(_url, _soup)


if __name__ == '__main__':
    print('direct link library')
