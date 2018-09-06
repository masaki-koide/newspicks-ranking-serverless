import json
import os
import requests
import urllib
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

top_url = 'https://newspicks.com/'
login_url = f'{top_url}login'
search_url = f'{top_url}search?'
bs_parser = 'html.parser'

session = None

def get_ranking(event, context):
    # セッションが既にあれば使い回す
    global session
    if not session:
        session = requests.session()

    # ログインチェック
    response = session.get(top_url)
    soup = BeautifulSoup(response.text, bs_parser)
    if not soup.select_one('.self'):
        login(session)

    # クエリを構築して検索
    params = event['queryStringParameters']
    param_range = params['range'] if params and 'range' in params else None
    query = urllib.parse.urlencode(dict({'sort': 'picks', 'q': ''}, **createDateQueryDict(param_range)))
    response = session.get(search_url + query)
    soup = BeautifulSoup(response.text, bs_parser)

    # 必要な情報を取得し、resultsに詰める
    cards = soup.select('.news-card-list > .search-result-card')
    results = [
        {
            'title': card.select_one('.news-title').text,
            'pick_count': card.select_one('.value').text,
            'url': urllib.parse.urljoin(top_url, card.select_one('.news-card > a').get('href'))
        }
        for card in cards
    ]
    # published = card.select_one('.published').text

    # TODO: bodyの中身を精査
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event,
        'results': results
    }

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*"
        },
        "body": json.dumps(body)
    }

    return response

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """

def login(session):
    logger.info('ログイン処理')
    data = {
        'username': os.environ['USERNAME'],
        'password': os.environ['PASSWORD']
    }
    session.post(login_url, data=data)

def createDateQueryDict(param_range):
    if not param_range:
        return {}

    days = {
        'day': 1,
        'week': 7,
        'month': 31,
        'half-year': 183,
        'year': 365
    }

    date_format = '%Y%m%d%H'
    JST = timezone(timedelta(hours=9), 'JST')
    now = datetime.now(JST)
    from_date = now - timedelta(days=days[param_range])

    return {
        'to': now.strftime(date_format),
        'from': from_date.strftime(date_format)
    }
