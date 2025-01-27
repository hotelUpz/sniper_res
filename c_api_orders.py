import time
import hmac
import json
import requests
import base64
from hashlib import sha256
from urllib.parse import urlencode
from b_log import Total_Logger
from b_log import Total_Logger
import inspect

# Класс для работы с API биржи Bitget
class ORDERS_API(Total_Logger):
    def __init__(self):
        super().__init__()
        self.bitget_api_public_key = self.config.get("keys").get('BITGET_API_PUBLIC_KEY')
        self.bitget_api_private_key = self.config.get("keys").get('BITGET_API_PRIVATE_KEY')
        self.bitget_api_passphrase = self.config.get("keys").get('BITGET_API_PASSPHRASE')
        self.base_url_bitget = "https://api.bitget.com"
        self.orders_endpoint_bitget = "/api/v2/spot/trade/place-order"
        self.orders_url_bitget = self.base_url_bitget + self.orders_endpoint_bitget
        self.order_data_endpoint = "/api/v2/spot/trade/orderInfo"

        self.bitget_headers = {
            "ACCESS-KEY": self.bitget_api_public_key,
            "ACCESS-SIGN": "",
            "ACCESS-TIMESTAMP": "",
            "ACCESS-PASSPHRASE": self.bitget_api_passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }
        self.session = None
        self.cookies = None
        # Декорируем методы с requests_connector
        methods_to_wrap = [
            method_name for method_name, _ in inspect.getmembers(self, predicate=inspect.ismethod)
            if not method_name.startswith("__")  # Исключаем специальные методы
        ]
        for method_name in methods_to_wrap:
            setattr(self, method_name, self.log_exceptions_decorator(getattr(self, method_name)))

    def init_session(self):
        self.session = requests.Session()

    def updating_session(self, response):
        # print("Fake request session was sending!")         
        self.cookies = response.cookies
        self.session.cookies.update(self.cookies)

    def requests_error_logger(self, resp, is_fake):
        if resp.status_code != 200 and not is_fake:
            print(f"Ошибка ордера: {resp.json()}")
            print(f"Статус код: {resp.status_code}")
        return resp    
    
    # public api //////////////
    def get_server_time(self):
        """
        Получает серверное время для заданной торговой площадки.
        """
        try:
            url = "https://api.bitget.com/api/v2/public/time"
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Ошибка при получении времени от Bitget: {response.status_code} - {response.text}")
                return None
            return int(response.json().get("data", {}).get('serverTime', 0))

        except requests.RequestException as e:
            print(f"Ошибка при получении серверного времени: {e}")
            return None
    
    # private api //////////////
    def place_bitget_market_order(self, symbol, size, side, is_fake):
        timestamp = str(int(time.time() * 1000))
        self.bitget_headers["ACCESS-TIMESTAMP"] = timestamp
        payload = {
            "symbol": symbol,
            "side": side,
            "orderType": 'MARKET',
            "size": str(size)
        }
        payload = {str(key): value for key, value in payload.items()}
        def generate_signature_bitget(timestamp, endpoint, payload):
            message = timestamp + 'POST' + endpoint + json.dumps(payload)
            signature = base64.b64encode(hmac.new(self.bitget_api_private_key.encode('utf-8'), message.encode('utf-8'), sha256).digest())
            return signature
        self.bitget_headers["ACCESS-SIGN"] = generate_signature_bitget(timestamp, self.orders_endpoint_bitget, payload)        
        resp = self.session.post(self.orders_url_bitget, headers=self.bitget_headers, json=payload)
        return self.requests_error_logger(resp, is_fake)
        
    def get_bitget_order_data(self, orderId):
        def sign_order_data_bitget(message, secret_key):
            mac = hmac.new(bytes(secret_key, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
            return base64.b64encode(mac.digest()).decode()

        def pre_hash(timestamp, method, request_path, body):
            return timestamp + method.upper() + request_path + body 
        
        timestamp = str(int(time.time() * 1000))        
        params = {"orderId": orderId}
        request_path = self.order_data_endpoint + '?' + urlencode(sorted(params.items()))
        body = ""
        message = pre_hash(timestamp, "GET", request_path, body)
        signature = sign_order_data_bitget(message, self.bitget_api_private_key)
        self.bitget_headers["ACCESS-SIGN"] = signature
        self.bitget_headers["ACCESS-TIMESTAMP"] = timestamp
        resp = self.session.get(self.base_url_bitget + request_path, headers=self.bitget_headers)

        return self.requests_error_logger(resp, False)

    def place_market_order(self, symbol, size, side, is_fake):  
        # print(symbol, size, side, is_fake)
        """Обобщенная функция для размещения ордеров на разных биржах."""
        resp = None
        resp = self.place_bitget_market_order(symbol, size, side, is_fake)        
        if is_fake:
            self.updating_session(resp)
        return resp