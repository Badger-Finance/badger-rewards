from helpers.constants import urls

import requests

def fetch_token_prices():
    response = requests.get("{}/prices".format(urls["staging"])).json()
    return response