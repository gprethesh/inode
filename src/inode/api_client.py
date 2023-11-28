import requests
import config


def get_current_block_height():
    response = requests.get(config.BLOCK_HEIGHT_API_URL)
    print("get_current_block_height called", response.json().get("blockheight"))
    return response.json().get("blockheight")


def get_dobby_emission(wallet_address):
    response = requests.get(f"{config.DOBBI_API_URL}?wallet={wallet_address}")
    print("get_dobby_emission called", response.json().get("emission"))
    return response.json().get("emission")


def get_coinbase_transactions(block_height):
    response = requests.get(f"{config.COINBASE_TX_API_URL}?block_height={block_height}")
    return response.json().get("transactions", [])
