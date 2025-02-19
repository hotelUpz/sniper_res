import time
import random
import re
import requests
from datetime import datetime, timedelta
from c_api_orders import ORDERS_API
from decimal import Decimal, getcontext, ROUND_DOWN
import pytz
import os
import inspect

current_file = os.path.basename(__file__)
getcontext().prec = 12  # Установите необходимую вам точность вычислений

class ParserUtils(ORDERS_API):
    def from_string_to_date_time(self, date_time_str):
        pattern = r'(\d{1,2})(?:st|nd|rd|th)? (\w+) (\d{4})(?:, (\d{1,2}):(\d{2}))? \(UTC\)'

        match = re.match(pattern, date_time_str)
        if match: 
            day = int(match.group(1))
            month_str = match.group(2)
            year = int(match.group(3))
            hour = int(match.group(4))
            minute = int(match.group(5))
            months = {
                'JANUARY': 1, 'FEBRUARY': 2, 'MARCH': 3, 'APRIL': 4, 'MAY': 5, 'JUNE': 6,
                'JULY': 7, 'AUGUST': 8, 'SEPTEMBER': 9, 'OCTOBER': 10, 'NOVEMBER': 11, 'DECEMBER': 12
            }
            month = months.get(month_str)
            if month:
                dt = datetime(year, month, day, hour, minute)
                milliseconds = int(dt.timestamp() * 1000)
                return milliseconds
        return

    def symbol_extracter(self, text):
        try:  
            unik_symbol_dict = {
                "（": ' (',
                "（ ": ' (',  
                '）': ') ',
                ' ）': ') ',  
                "( ": '(',
                " )": ')',
            } 

            for k, v in unik_symbol_dict.items():
                text = text.replace(k, v)  
            matches = re.findall(r'\((.*?)\)', text)
            return [re.sub(r'[\(\)\.,\-!]', '', match) for match in matches] 
        except:
            pass
        return []

class TimeUtils(ParserUtils): 
    # def get_current_ms_utc_time(self):
    #     return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    def get_current_ms_utc_time(self):
        return int(time.time() * 1000)

    def get_start_of_day(self, days=5):
        now = datetime.now()
        start_of_day = datetime(now.year, now.month, now.day) - timedelta(days=days)
        return int(start_of_day.timestamp() * 1000)

    def milliseconds_to_datetime(self, milliseconds):
        seconds = milliseconds / 1000
        dt = datetime.fromtimestamp(seconds, pytz.utc).astimezone(self.tz_location)
        return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{int(milliseconds % 1000):03d}"  

    def measure_network_delay(self, test_url="https://api.bitget.com/api/v2/public/time"):
        network_delay_ms = 0
        for _ in [1,2]:
            start_time = self.get_current_ms_utc_time()
            requests.get(test_url)  # Тестовый запрос
            end_time = self.get_current_ms_utc_time()
            network_delay_ms += (end_time - start_time) // 2  # Половина времени запроса
            time.sleep(0.5)
            
        return int(network_delay_ms/2)
        
    def time_waiter(self, target_time_ms):
        # Основное ожидание
        while (current_time := self.get_current_ms_utc_time()) + 2 < target_time_ms:
            sleep_time = (target_time_ms - current_time) / 1000
            time.sleep(min(sleep_time, 0.001))  # Уступаем другим задачам

        # Точная синхронизация (улучшенная версия busy-waiting)
        while self.get_current_ms_utc_time() < target_time_ms:
            pass
    
    def universal_sleeping(self, listing_time, left_min):
        delta_time = listing_time - self.get_current_ms_utc_time()
        left_time = left_min* 60* 1000
        if delta_time > left_time:
            self.time_waiter(listing_time - left_time)            
            return True
        else:
            self.log_info_loger(f"Дельта времени: {delta_time}")
            self.log_info_loger("Нестыковки по времени.") 

        return False 

    def sync_time(self, num_requests=2):
        time_diffs = []
        wrong_req_counter = 0
        
        for _ in range(num_requests):
            start_time = self.get_current_ms_utc_time()
            server_time = self.get_server_time()
            
            if isinstance(server_time, (int, float)):
                end_time = self.get_current_ms_utc_time()
                request_duration = end_time - start_time
                time_diff = server_time - (start_time + request_duration / 2)
                time_diffs.append(time_diff)
                time.sleep(random.uniform(0.2, 1.0))
            else:
                wrong_req_counter += 1
                
        valid_time_diff_count = len(time_diffs)
        
        # Возвращаем среднее временное смещение, если есть действительные значения
        if valid_time_diff_count > 0:
            return sum(time_diffs) / valid_time_diff_count
        else:
            return 0

    def work_sleep_manager(self):
        if (not self.work_to and self.sleep_to):
            return None
        
        # Получаем текущее время в указанной временной зоне
        current_time = datetime.now(self.tz_location)
        current_hour = current_time.hour
        
        # Проверяем, находится ли текущее время в периоде отдыха
        if not (self.sleep_to <= current_hour < self.work_to):
            # Определяем время следующего пробуждения
            desired_time = current_time.replace(hour=self.sleep_to, minute=0, second=0, microsecond=0)
            
            # Если время уже наступило сегодня, устанавливаем на следующий день
            if current_hour >= self.sleep_to:
                desired_time += timedelta(days=1)
            
            # Вычисляем разницу во времени
            time_diff_seconds = (desired_time - current_time).total_seconds()
            print("It is time to rest! Let's go to bed!")
            return time_diff_seconds
        
        return None

class ProcessUtils(TimeUtils):
    def __init__(self):
        super().__init__()      
        
        # Декорируем методы с requests_connector
        methods_to_wrap = [
            method_name for method_name, _ in inspect.getmembers(self, predicate=inspect.ismethod)
            if not method_name.startswith("__")  # Исключаем специальные методы
        ]
        for method_name in methods_to_wrap:
            setattr(self, method_name, self.log_exceptions_decorator(getattr(self, method_name)))
    
    def process_order_response(self, place_market_order_resp):
        """Проверяет и возвращает данные запроса и статус."""
        if place_market_order_resp is not None:
            try:
                return place_market_order_resp.json(), place_market_order_resp.status_code
            except Exception as ex:
                self.log_error_loger(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")                
        return None, None
        
    def print_order_data(self, place_market_order_resp_j, status):
        """Печатает данные ордера или ошибку."""
        if not isinstance(place_market_order_resp_j, dict):
            print(f"Ошибка при создании ордера. Текст ошибки: {status}")
            return
        
        order_details = "\n".join(f"{k}: {v}" for k, v in place_market_order_resp_j.items())
        # Время транзакции для Bitget
        timestamp = place_market_order_resp_j.get("requestTime")

        # Проверяем и конвертируем timestamp в дату
        if timestamp:
            try:
                now_time = self.milliseconds_to_datetime(int(timestamp))
            except ValueError:
                print(f"Неверный формат времени: {timestamp}")
                now_time = None
        else:
            now_time = None

        # Печать результатов
        print(f'Время транзакции: {now_time}')
        print(f"Данные ордера:\nСтатус ответа: {status}\n{order_details}\n")

    def adjust_quantity(self, quantity: Decimal, share_percent: Decimal) -> Decimal:
        """Корректируем количество в зависимости от его значения."""
        adjusted_quantity = (share_percent / Decimal(100)) * quantity

        if quantity >= Decimal(20):
            # Умножаем на 0.99 и округляем вниз для целого значения.
            return (adjusted_quantity * Decimal('0.99')).to_integral_value(rounding=ROUND_DOWN)
        elif Decimal('1') < quantity < Decimal('20'):
            # Округляем до целого вниз.
            return adjusted_quantity.to_integral_value(rounding=ROUND_DOWN)
        else:
            # Для небольших значений оставляем точность до 8 знаков.
            return adjusted_quantity * Decimal('0.99').quantize(Decimal('0.00000001'), rounding=ROUND_DOWN)


    def calculate_quantity(self, fills, key="qty"):
        """Вспомогательная функция для расчета количества."""
        try:
            return sum(Decimal(fill.get(key, 0)) for fill in fills)
        except Exception as ex:
            self.log_error_loger(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
            return 0

    def qty_extracter(self, response):
        """Извлекает количество и стоимость продажи (в USDT) для указанной биржи."""
        qty = Decimal(0)
        price = Decimal(0)
        usdt_value = Decimal(0)

        try:
            bitget_order_id = response.get('data', {}).get('orderId')
            if bitget_order_id is None:
                self.log_info_loger("Проблемы при попытке получить данные ордера")
                return 0, 0, 0

            for attempt in range(1, 3):  # Три попытки получить данные
                get_data_resp = self.get_bitget_order_data(bitget_order_id)
                get_data_order_data, get_data_status = self.process_order_response(get_data_resp)

                if get_data_status == 200 and get_data_order_data:
                    fills = get_data_order_data.get("data", [])
                    qty = self.calculate_quantity(fills, key="baseVolume")  # Получаем количество
                    price = sum(Decimal(fill['priceAvg']) for fill in fills)
                    usdt_value = sum(Decimal(fill['quoteVolume']) for fill in fills)  # Прямо из данных берем значение в USDT
                    if qty != 0:
                        break
                else:
                    self.log_info_loger(f"Проблемы при получении данных ордера. Попытка: {attempt}")
                    time.sleep(0.1)

            return qty, usdt_value, price

        except Exception as ex:
            self.log_error_loger(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
            return 0, 0, 0

    def result_logger(self, place_market_order_resp_list, symbol):
        # Initialize totals and counters
        total_buy_qty = total_buy_usdt = acum_buy_price = Decimal(0)
        total_sell_qty = total_sell_usdt = acum_sell_price = Decimal(0)
        progress_counter_buy = progress_counter_sell = Decimal(0)

        # Process market order responses
        if place_market_order_resp_list:
            for order_data, status, side in place_market_order_resp_list:
                try:
                    self.print_order_data(order_data, status)
                    qty, usdt_value, price = self.qty_extracter(order_data)

                    if qty > 0:
                        if side == "BUY":
                            progress_counter_buy += 1
                            total_buy_qty += Decimal(qty)
                            total_buy_usdt += Decimal(usdt_value)
                            acum_buy_price += Decimal(price)
                        elif side == "SELL":
                            progress_counter_sell += 1
                            total_sell_qty += Decimal(qty)
                            total_sell_usdt += Decimal(usdt_value)
                            acum_sell_price += Decimal(price)

                except Exception as ex:
                    self.log_error_loger(
                        f"Ошибка: {ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}"
                    )

        # Calculate progress, averages, and profit
        in_plane_buy = sum(1 for x in place_market_order_resp_list if x[2] == "BUY")
        in_plane_sell = sum(1 for x in place_market_order_resp_list if x[2] == "SELL")

        progress_per_buy = (progress_counter_buy * 100 / in_plane_buy) if in_plane_buy else 0
        progress_per_sell = (progress_counter_sell * 100 / in_plane_sell) if in_plane_sell else 0

        average_buy_price = (acum_buy_price / progress_counter_buy) if progress_counter_buy else Decimal(0)
        average_sell_price = (acum_sell_price / progress_counter_sell) if progress_counter_sell else Decimal(0)

        profit_usdt = total_sell_usdt - total_buy_usdt
        profit_per = ((acum_sell_price - acum_buy_price) / acum_buy_price * 100) if acum_buy_price > 0 else Decimal(0)
        left_tokens = total_sell_qty - total_buy_qty

        # Логирование результатов
        self.log_info_loger(
            f"Результаты торгов символа {symbol}:\n"
            f"Куплено токенов: {total_buy_qty}, Средняя цена покупки: {average_buy_price}, "
            f"Сумма покупки в USDT: {total_buy_usdt}, Прогресс покупок: {progress_per_buy}%\n"
            f"Продано токенов: {total_sell_qty}, Средняя цена продаж: {average_sell_price}, "
            f"Сумма продаж в USDT: {total_sell_usdt}, Прогресс продаж: {progress_per_sell}%\n"
            f"Профит в USDT: {profit_usdt}\n"
            f"Профит в %: {profit_per}\n"
            f"Осталось токенов: {left_tokens}\n"
        )

# print(TimeUtils().work_sleep_manager())