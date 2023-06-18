import requests
import datetime
import pickle

def load_crypto_list():
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url)
    data = response.json()
    crypto_list = []
    for item in data:
        symbol = item['symbol']
        if symbol.endswith('BTC'):
            crypto = symbol[:-3].replace('-', ' - ')
            crypto_list.append(crypto)
    return crypto_list

def get_crypto_data(crypto, start_timestamp, end_timestamp):
    symbol = f"{crypto}USDT"
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&startTime={start_timestamp}&endTime={end_timestamp}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error retrieving data: {response.status_code}")
        return None

    data = response.json()

    crypto_data = []
    for item in data:
        try:
            if not isinstance(item[0], int):
                continue
            timestamp = item[0] / 1000
            open_price = item[1]
            close_price = item[4]
            crypto_data.append((timestamp, open_price, close_price))
        except (ValueError, IndexError, AttributeError):
            continue

    return crypto_data

def save_selected_crypto(selected_crypto):
    with open("selected_crypto.pickle", "wb") as f:
        pickle.dump(selected_crypto, f)

def load_selected_crypto():
    try:
        with open("selected_crypto.pickle", "rb") as f:
            selected_crypto = pickle.load(f)
            return selected_crypto
    except (FileNotFoundError, EOFError):
        return []

def get_timestamp(date):
    return int(date.timestamp()) * 1000
