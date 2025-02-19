    
    # def milliseconds_to_datetime_for_parser(self, milliseconds):        
    #     seconds, milliseconds = divmod(milliseconds, 1000)
    #     time = datetime.datetime.utcfromtimestamp(seconds)        
    #     return time.strftime('%Y-%m-%d %H:%M:%S')

    # def work_sleep_manager(self):
    #     if not self.work_to or not self.sleep_to:
    #         return None
    #     current_time_utc = time.gmtime(time.time())
    #     current_hour = current_time_utc.tm_hour
    #     if not (self.sleep_to <= current_hour < self.work_to):
    #         current_time_utc = time.gmtime(time.time())
    #         desired_time_utc = time.struct_time((current_time_utc.tm_year, current_time_utc.tm_mon, current_time_utc.tm_mday + 1, self.sleep_to, 0, 0, 0, 0, 0))
    #         time_diff_seconds = time.mktime(desired_time_utc) - time.mktime(current_time_utc)
    #         print("It is time to rest! Let's go to bed!")
    #         return time_diff_seconds
    #     return None


# from datetime import datetime, timezone
# import time

# # current_utc_time_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
# print(int(datetime.now(timezone.utc).timestamp() * 1000))
# print(int(time.time()* 1000))


    # def get_current_ms_utc_time(self):
    #     return int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    # def date_of_the_month(self):        
    #     current_time = time.time()        
    #     datetime_object = datetime.fromtimestamp(current_time)       
    #     formatted_time = datetime_object.strftime('%d')
    #     return int(formatted_time)

    # def datetime_to_milliseconds(self, datetime_str):
    #     dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    #     dt_obj = self.tz_location.localize(dt_obj)
    #     return int(dt_obj.timestamp() * 1000)
    
    # def get_date_time_now(self, tz_location):
    #     now = datetime.now(tz_location)
    #     return now.strftime("%Y-%m-%d %H:%M:%S")

    # # ///////////////////////////////
    # def get_start_of_day(self, days=1):
    #     now = datetime.now()
    #     start_of_day = datetime(now.year, now.month, now.day) - timedelta(days=days)
    #     return int(start_of_day.timestamp() * 1000)

# sell_params = {
#             1: {
#                 "delay_sec": 0.5, # seconds
#                 "share_%": 100
#             }
#         }

# for _, val in sell_params.items():
#     print(val.get("share_%"))


# from joblib import Parallel, delayed

# def links_multiprocessor(self, data, cur_time, cpu_count=1): 
#     total_list = []
#     try:
#         res = Parallel(n_jobs=cpu_count, prefer="threads")(delayed(lambda item: self.bitget_links_handler(item, cur_time))(item) for item in data)
#         for x in res: 
#             if x:               
#                 try:                    
#                     total_list.append(x)
#                 except:
#                     pass 
#     except:
#         pass
#     return total_list