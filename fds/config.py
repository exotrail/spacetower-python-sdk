import os
from loguru import logger


class Config:
    api_key = os.getenv('FDS_API_KEY', None)
    api_url = os.getenv('FDS_API_URL', "https://api.spacetower.exotrail.space/fds/v1")


def set_api_key(token: str):
    logger.debug(f'API key set to {token}')
    Config.api_key = token


def get_api_key():
    logger.debug(f'get_api_key -> {Config.api_key}')
    return Config.api_key


def set_url(url: str):
    logger.debug(f'API URL set to {url}')
    Config.api_url = url


def get_api_url():
    return Config.api_url
