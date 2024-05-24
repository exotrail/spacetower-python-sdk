import os


class Config:
    api_key = os.getenv('FDS_API_KEY', '')
    api_url = os.getenv('FDS_API_URL', "https://api.spacetower.exotrail.space/fds/v1")


def set_api_key(token: str):
    Config.api_key = token


def get_api_key():
    return Config.api_key


def set_url(url: str):
    Config.api_url = url


def get_api_url():
    return Config.api_url
