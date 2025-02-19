import pytz

class Settings():
    test = False
    config = {
        "network_delay_ms": -100,
        "buy_size": 5.0, # usdt
        "sell_params": {
            1: {
                "delay_ms": 500, # mili_seconds
                "share_%": 100
            }
        },
        "keys": {
            "BITGET_API_PUBLIC_KEY": "bg_92c0954ee40dd1776d9281aeccbb7701",
            "BITGET_API_PRIVATE_KEY": "7c6893ea1e69bbb978577848946912a48caa24e219f743bf606025643a449440",
            "BITGET_API_PASSPHRASE": "hereiame33"
        },
        "is_bible_quotes": True,        
        "is_sync": False,
        "sleep_to": 8,
        "work_to": None,
        "tz_location_str": "Europe/Kyiv",
    }

    def __init__(self):
        self.buy_size = self.config.get("buy_size", 0)
        self.network_delay_ms = self.config.get("network_delay_ms", None)
        self.sell_params = self.config.get("sell_params", {})
        self.is_bible_quotes = self.config.get("is_bible_quotes")
        self.is_sync = self.config.get("is_sync")
        self.work_to, self.sleep_to = self.config.get("work_to", None), self.config.get("sleep_to", None)       
        self.tz_location = pytz.timezone(self.config.get("tz_location_str"))

# Settings()
