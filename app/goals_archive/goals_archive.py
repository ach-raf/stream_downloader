import logging
import os
import sqlite3
import configparser
import praw
from urllib.parse import urlparse
import requests
import json
from reddit_goal import RedditGoal
from datetime import datetime

# =================================================================================================
CURRENT_DIR_PATH = os.path.dirname(os.path.realpath(__file__))

API_LINK = 'http://104.156.140.246:8888/api/'

AVAILABLE_SOURCES = ['streamable', 'streamja',
                     'streamye', 'streamvi', 'streamwo', 'mixture', 'streamff', 'clippituser', 'streamgg', 'fodder']

DATABASE_NAME = 'reddit_goals.db'

TABLE_NAME = 'goals'

DATABASE_LOCATION = os.path.join(CURRENT_DIR_PATH, DATABASE_NAME)

CONFIG_FILE = os.path.join(CURRENT_DIR_PATH, 'config.ini')

CONNECTION = sqlite3.connect(DATABASE_LOCATION)

# add it to logging.basicConfig to change output from console to a log file, filename=LOG_LOCATION
logging.basicConfig(
    format="%(levelname)s:%(message)s", encoding="utf-8", level=logging.INFO
)

logger = logging.getLogger(__name__)
# =================================================================================================


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
        for key in config[section]:
            # print(f'{key} = {config[section][key]}')
            credentials[key] = config[section][key]
    return credentials


def get_reddit(_config_path):

    info_config = read_info_file(_config_path)
    client_id = info_config['client_id']
    client_secret = info_config['client_secret']
    user_agent = info_config['user_agent']
    reddit_username = info_config['reddit_username']
    reddit_password = info_config['reddit_password']

    _reddit = praw.Reddit(client_id=client_id,
                          client_secret=client_secret,
                          user_agent=user_agent,
                          username=reddit_username,
                          password=reddit_password)

    return _reddit


def database_excute_command(_command, _fetch_type="none"):
    """use this function to interact with the database

    Args:
        _command (str): the sql command to be excuted
        _fetch_type (str, optional): [either none, fetch_one or fetch_all]. Defaults to 'none'.
    """

    with sqlite3.connect(DATABASE_LOCATION) as _connection:
        try:
            _cursor = _connection.cursor()
            match _fetch_type.lower():
                case "none":
                    result = _cursor.execute(_command)
                case "fetch_one":
                    result = _cursor.execute(_command).fetchone()
                case "fetch_all":
                    result = _cursor.execute(_command).fetchall()
            return result
        except sqlite3.Error as e:
            logger.warninging(_command)
            logger.warninging(e)
            return False
        finally:
            _connection.commit()
            _cursor.close()


def check_table_exists(_table_name):
    sql_command = f''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{_table_name}' '''
    _rows = database_excute_command(sql_command, 'fetch_one')
    if _rows[0] == 1:
        logger.info(f'{_table_name} table found')
        return True
    else:
        logger.info(f'{_table_name} table not found')
        return False


def check_item_exists(post_id):
    sql_command = f''' SELECT title from {TABLE_NAME} where id = "{post_id}" '''
    _row = database_excute_command(sql_command, 'fetch_one')
    if _row:
        return _row[0]
    else:
        return False


def set_up_database():
    if not check_table_exists(TABLE_NAME):
        logger.info(f'creating {TABLE_NAME} table')
        _sql_command = f'''CREATE TABLE {TABLE_NAME} (id TEXT NOT NULL  PRIMARY KEY, title TEXT, url TEXT, direct_url TEXT, created_utc INT) '''
        result = database_excute_command(_sql_command)


def insert_item(_reddit_goal):
    _reddit_goal.title = _reddit_goal.title.replace('"', "'")
    _insert_command = f'INSERT INTO {TABLE_NAME} VALUES ("{_reddit_goal.id}", "{_reddit_goal.title}", "{_reddit_goal.url}", "{_reddit_goal.direct_url}", "{_reddit_goal.created_utc}")'
    insertion_details = database_excute_command(_insert_command)
    return insertion_details


def site_name(_url):
    _site_name = urlparse(_url)
    if 'www' not in str(_site_name.netloc):
        _site_name = str(_site_name.netloc).split('.')[0]
    else:
        _site_name = str(_site_name.netloc).split('.')[1]
    return _site_name


def clean_request(_url):
    _site_name = site_name(_url)
    _id = _url.replace('https://', '').split('/')[-1]
    return f'{_site_name}?id={_id}'


def get_stream_link(_url):

    _request = clean_request(_url)
    logger.info(f'Request{_request}')
    _url = f'{API_LINK}{_request}'
    logger.info(_url)
    _response = requests.get(_url).text
    if 'direct_link' in _response:
        return json.loads(_response)['direct_link']
    else:
        return False


def humanize_unixtime(unix_time):
    return datetime.fromtimestamp(int(unix_time)).strftime('%d-%m-%Y %H:%M')


def get_date_from_utc_time(utc_time):
    return datetime.fromtimestamp(int(utc_time)).strftime('%d-%m-%Y')


def update_url(_reddit_goal):
    _update_command = f"UPDATE {TABLE_NAME} SET direct_url = '{_reddit_goal.direct_url}' WHERE id = '{_reddit_goal.id}' "
    insertion_details = database_excute_command(_update_command)
    return insertion_details


def update_direct_sources():
    _number_of_updates = 10
    for source in AVAILABLE_SOURCES:
        sql_command = f''' SELECT * from {TABLE_NAME} WHERE url LIKE '%{source}%' ORDER BY created_utc DESC LIMIT {_number_of_updates}'''
        _rows = database_excute_command(sql_command, 'fetch_all')
        for row in _rows:
            _goal = RedditGoal(row[0], row[1],
                               row[2], row[3], row[4])

            new_link = get_stream_link(_goal.url)
            _goal.direct_url = new_link
            update = update_url(_goal)
            if update:
                logger.info(f'{_goal.title} updated in the database')
            else:
                logger.info(f'could not update {_goal.title}')


def teams_collection():
    _query_limit = 200
    sql_command = f''' SELECT * from {TABLE_NAME} ORDER BY created_utc DESC LIMIT {_query_limit}'''
    _rows = database_excute_command(sql_command, 'fetch_all')
    current_day = datetime.now().strftime('%d-%m-%Y')
    dates_collection = set()
    for row in _rows:
        _goal = RedditGoal(row[0], row[1], row[2], row[3], row[4])
        _goals_date = get_date_from_utc_time(_goal.created_utc)
        if _goals_date:
            dates_collection.add(_goals_date)
            logger.info(f'{_goals_date} - {_goal.title}')
    logger.info(f'{dates_collection}')
    goals_dict = {}
    for date in dates_collection:
        goals_collection = []
        for row in _rows:
            _goal = RedditGoal(row[0], row[1], row[2], row[3], row[4])
            _goals_date = get_date_from_utc_time(_goal.created_utc)
            if _goals_date == date:
                goals_collection.append(_goal)
        goals_dict[date] = goals_collection
    # logger.info(f'{goals_dict[current_day]}')
    try:
        for goal in goals_dict[current_day]:
            logger.info(f'{goal.title}')
    except KeyError:
        logger.warning('No goals for current day')


def main():
    reddit = get_reddit(CONFIG_FILE)
    sub_reddit = reddit.subreddit('soccer')
    new = sub_reddit.new(limit=25)
    for submission in new:
        if site_name(submission.url) in AVAILABLE_SOURCES:
            if not check_item_exists(submission.id):
                _direct_link = get_stream_link(submission.url)
                goal = RedditGoal(submission.id, submission.title,
                                  submission.url, _direct_link, int(submission.created_utc))

                insertion = insert_item(goal)
                if insertion:
                    logger.info(f'{goal.title} Added to database')
                else:
                    logger.info(f'could not add {goal.title} to database')


if __name__ == '__main__':
    set_up_database()
    # teams_collection()
    main()
    # update_direct_sources()
