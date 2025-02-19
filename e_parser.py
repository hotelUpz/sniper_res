import requests
import cloudscraper
from bs4 import BeautifulSoup
import time 
import random
from random import choice
from d_utils import ProcessUtils

parse_url_api = "https://api.bitget.com/api/v2/public/annoucements?&annType=coin_listings&language=en_US"

class BitgetParser(ProcessUtils):
    def links_multiprocessor(self, data, cur_time): 
        total_list = []

        for item in data:
                try:                    
                    total_list.append(self.bitget_links_handler(item, cur_time))                    
                except:
                    pass 
                time.sleep(random.uniform(0.5, 2.5))  

        return total_list

    def bitget_links_handler(self, data_item, cur_time):
        try:
            url=data_item['annUrl']
            scraper = cloudscraper.create_scraper()
            r = scraper.get(url)

            if r is None or r.status_code != 200:
                print(r)
                return {}

            soup = BeautifulSoup(r.text, 'html.parser')
            listing_time_all_potential_string = soup.find('div', class_='ArticleDetails_actice_details_main__oIjfu').get_text()
            trading_time_str = [x for x in listing_time_all_potential_string.split('\n') if "TRADING AVAILABLE:" in x.upper()]
            if not trading_time_str:
                return {}
            trading_time_str = trading_time_str[0].upper().replace("TRADING AVAILABLE:", "").strip()
            listing_time = self.from_string_to_date_time(trading_time_str) 
            # print(f"listing_time: {listing_time}")
            # print(data_item['annUrl'])

            if listing_time and listing_time > cur_time:
                symbol_data = self.symbol_extracter(data_item['annTitle'])
                # print(symbol_data)
                if symbol_data:
                    symbol = None
                    symbol = [x.strip() + 'USDT' for x in symbol_data if x.strip()][0]
                    return {                                
                                "symbol": symbol,                                
                                "listing_time_ms": listing_time      
                            }
               
        except Exception as ex:
            print(ex)
                   
        return {}
                 
    def bitget_parser(self):
        try: 
            start_day = self.get_start_of_day()                 
            r = requests.get(parse_url_api)
            if r is None or r.status_code != 200:
                return {}
            data = r.json()
            data = data["data"] 
            if data:
                # print(data)
                data = [{**x, "cTime": int(float(x["cTime"]))} for x in data if int(float(x["cTime"])) > start_day]  
            # print(data)
            if not data: 
                return {}  
            cur_time = self.get_current_ms_utc_time()  
            pars_data = [x for x in self.links_multiprocessor(data, cur_time) if x and x.get("listing_time_ms")]
            # return pars_data
            set_list = sorted(pars_data, key=lambda x: x.get("listing_time_ms", 0), reverse=False)
            return set_list[0] if set_list else {}

        except Exception as ex:
            print(f"Error in file parser.py str ~ 100: {ex}")            
            return {}
    
# print(BitgetParser().bitget_parser())


