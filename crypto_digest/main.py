import os
import logging
from datetime import datetime, timezone
import requests
from typing import List
from pydantic import BaseModel

from .email_template import build_subject, render_digest
from .notifier import NotificationManager

URL = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
api_key = os.environ['API_KEY']

# implement custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler('event.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler.setFormatter(formatter)
logger.addHandler(handler)


# model response data
class CoinData(BaseModel):
    coin_name: str
    coin_price: float
    volume_change_24h: float
    percentage_change_24h: float
    percentage_change_7d: float
    percentage_change_30d: float


class CoinDataResponse(BaseModel):
    coins: List[CoinData]


def fetch_data():
    # fetch data from api
    header = {
        'X-CMC_PRO_API_KEY': api_key
    }
    query = {
        'start': 1,
        'limit': 5
    }

    response = requests.get(url=URL, headers=header, params=query)
    response.raise_for_status()
    if response.status_code == 200:
        data = response.json()

        coin_data_response = CoinDataResponse(
            coins=[CoinData(
                coin_name=coin['name'],
                coin_price=coin['quote']['USD']['price'],
                volume_change_24h=coin['quote']['USD']['volume_change_24h'],
                percentage_change_24h=coin['quote']['USD']['percent_change_24h'],
                percentage_change_7d=coin['quote']['USD']['percent_change_7d'],
                percentage_change_30d=coin['quote']['USD']['percent_change_30d']

            ) for coin in data['data']]
        )

        # send email and log event
        generated_at = datetime.now(timezone.utc)
        digest = render_digest(coin_data_response.coins, generated_at=generated_at)
        notification_manager = NotificationManager()
        if notification_manager.send_email(
            subject=build_subject(generated_at),
            text_body=digest.text_body,
            html_body=digest.html_body,
        ):
            logger.info("email sent successfully")


if __name__ == '__main__':
    fetch_data()
