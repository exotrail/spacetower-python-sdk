import os

def set_token(token: str):
    os.environ['FDS_API_TOKEN'] = token

def set_url(url: str):
    os.environ['FDS_API_URL'] = url

def get_api_url():
    return os.getenv("FDS_API_URL", "https://api.spacetower.exotrail.space/fds/v1")

def get_api_token():
    return os.getenv("FDS_API_TOKEN", "")