import time
from datetime import datetime, timezone
import sys
from e_parser import BitgetParser
from decimal import Decimal, getcontext, ROUND_DOWN
import os
import inspect

current_file = os.path.basename(__file__)
getcontext().prec = 12  # Установите необходимую вам точность вычислений

def gen_bible_quote():
    random_bible_list = [
        "<<Благодать Господа нашего Иисуса Христа, и любовь Бога Отца, и общение Святаго Духа со всеми вами. Аминь.>>\n___(2-е Коринфянам 13:13)___",
        "<<Притом знаем, что любящим Бога, призванным по Его изволению, все содействует ко благу.>>\n___(Римлянам 8:28)___",
        "<<Спокойно ложусь я и сплю, ибо Ты, Господи, един даешь мне жить в безопасности.>>\n___(Пс 4:9)___"
    ]
    
    current_hour = datetime.now().hour
    if 6 <= current_hour < 12:
        return random_bible_list[0]
    elif 12 <= current_hour < 23:
        return random_bible_list[1]
    return random_bible_list[2]

def get_test_utc_time(minute_num):
    # Получаем текущее время в UTC
    now = datetime.now(timezone.utc)

    # Вычисляем ближайшее время, кратное минуте в миллисекундах
    utc_milliseconds = int((now.timestamp() // 60 + 1) * 60 * 1000) + (60000* minute_num)

    return utc_milliseconds
        
class MAIN_LOGIC(BitgetParser):
    def trading_logic_template(self, symbol, listing_ms_time):
        order_resp_list = []
        inaccuracy_ms = 100

        # buy logic:
        try:
            buy_order_data = None

            waiting_before_min = 1
            if not self.universal_sleeping(listing_ms_time, waiting_before_min):
                return
            # ///////////////
            time_offset = 0
            if self.is_sync:
                time_offset = self.sync_time()            
            
            # //////////////
            if not self.network_delay_ms:
                self.network_delay_ms = -self.measure_network_delay() + inaccuracy_ms

            print(f"time_offset: {time_offset}")
            print(f"self.network_delay_ms: {self.network_delay_ms}")            
            
            waiting_before_min = 0.25
            if not self.universal_sleeping(listing_ms_time, waiting_before_min):
                return
            
            self.init_session()
            fake_resp = self.place_market_order("abracadabra", self.buy_size, "BUY", True)
            self.updating_session(fake_resp)

            open_ms_time = listing_ms_time - time_offset
            open_ms_time += self.network_delay_ms
            self.time_waiter(open_ms_time)  

            buy_market_order_resp = self.place_market_order(symbol, self.buy_size, "BUY", False)
            buy_order_data, buy_status = self.process_order_response(buy_market_order_resp)
            if not buy_order_data or buy_status != 200:
                self.log_info_loger("Проблемы при попытке создать ордер на покупку", True)
                print(buy_order_data)
                return False
            
            order_resp_list.append((buy_order_data, buy_status, "BUY"))         
        except Exception as ex:
            self.log_error_loger("Проблемы при попытке создать ордер на покупку:", True)
            self.log_error_loger(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")                
        
        # sell logic:
        if not order_resp_list:
            return False 
        
        total_size = Decimal(0)
        for buy_order_data, _, _ in order_resp_list:
            try:
                total_item_size, _, _ = self.qty_extracter(buy_order_data)
                total_size += total_item_size
            except Exception as ex:
                self.log_error_loger("Проблемы при попытке извлечь данные о покупке:", True)
                self.log_error_loger(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")
        i = 0
        for _, val in self.sell_params.items():
            try:
                sell_order_data, sell_status = None, 0
                share_percent, delay_ms = Decimal(val.get("share_%")), val.get("delay_ms")
                i+= 1
                if i == 1:
                    next_target_ms = listing_ms_time + delay_ms
                    cur_time = self.get_current_ms_utc_time()
                    if cur_time - next_target_ms > 10:
                        self.time_waiter(next_target_ms)                

                size = self.adjust_quantity(total_size, share_percent)                    
                place_market_order_resp = self.place_market_order(symbol, size, 'SELL', False)               
                sell_order_data, sell_status = self.process_order_response(place_market_order_resp)
                if not sell_order_data or sell_status != 200:
                    self.log_info_loger("Проблемы при попытке создать ордер на продажу", True) 
                    continue   

                order_resp_list.append((sell_order_data, sell_status, "SELL"))   
                if i > 1:
                    time.sleep(delay_ms/ 1000)             
            except Exception as ex:
                self.log_error_loger("Проблемы при попытке создать ордер на продажу:", True)
                self.log_error_loger(f"{ex} на строке {inspect.currentframe().f_lineno} в файле {current_file}")

        self.result_logger(order_resp_list, symbol)
        
        return True

    def trading_monitoring(self):
        first_iter = True

        if self.is_bible_quotes:
            print(gen_bible_quote())

        while True:
            try:
                # Проверяем, нужно ли спать
                time_diff_seconds = self.work_sleep_manager()
                if time_diff_seconds:
                    print(f"Время спать {time_diff_seconds} секунд...")
                    time.sleep(time_diff_seconds)
                    continue
                
                if first_iter:
                    first_iter = False
                    print("Время поработать!")

                # --- Парсинг данных ---
                parse_data = self.bitget_parser()
                if not parse_data:
                    print("Не найдено ни одной монеты. Ждём 30 минут...")
                    time.sleep(1800)
                    continue

                symbol = parse_data.get('symbol')
                listing_time_ms = parse_data.get('listing_time_ms')

                # Проверяем, не слишком ли рано
                remaining_time = listing_time_ms - self.get_current_ms_utc_time()
                if remaining_time >= 3_600_000:
                    print(f"Монета {symbol} найдена, но еще не вечер... Ждём 30 минут.")
                    time.sleep(1800)
                    continue

                print(f"🎯 Найдена монета: {symbol}")
                print(f"🕒 Время листинга: {self.milliseconds_to_datetime(listing_time_ms)}")

                # Запускаем торговую логику
                if not self.trading_logic_template(symbol, listing_time_ms):
                    print("*** Ошибки при торговле: ***")
                    print(self.log_info_list)
                    print(self.general_error_logger_list)
                    return False
                
            except Exception as e:
                print(f"❌ Ошибка в цикле: {e}")

            # Логируем в конце итерации
            print("*** Отчёт ***")
            print(self.log_info_list)
            print(self.general_error_logger_list)

            # Засыпаем перед следующей итерацией
            time.sleep(60)
        
def main():
    main_logic_instanse = MAIN_LOGIC()
    # intro_answer = input('Начинаем? (y/n)').strip()
    # print()
    # if intro_answer == "y":     
    if not main_logic_instanse.trading_monitoring():
        print("Ошибка в работе бота.")
    input('Завершить работу? (Enter)')
    print("Работа программы завершена")
    time.sleep(1)
    sys.exit()    

if __name__ == "__main__":
    main()