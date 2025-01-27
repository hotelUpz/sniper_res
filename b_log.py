from a_SETTINGS import Settings
import asyncio
import os
import inspect

current_file = os.path.basename(__file__)

class Total_Logger(Settings):
    log_info_list = []
    general_error_logger_list = []
    async_lock = asyncio.Lock()
    
    def log_info_loger(self, data, is_print=False):
        self.log_info_list.append(data)
        if is_print:
            print(data)

    def log_error_loger(self, data, is_print=False):
        self.general_error_logger_list.append(data)
        if is_print:
            print(data)

    def log_exception(self, ex):
        """Логирование исключений с указанием точного места ошибки."""
        # Получаем информацию об ошибке
        exception_message = str(ex)
        # Получаем стек вызовов
        stack = inspect.trace()
        
        # Берем последний фрейм, который соответствует месту, где произошла ошибка
        if stack:
            last_frame = stack[-1]
            file_name = last_frame.filename
            line_number = last_frame.lineno
            func_name = last_frame.function
            
            message = f"Error occurred in '{func_name}' at file '{file_name}', line {line_number}: {exception_message}"
            # print(message)
            self.general_error_logger_list.append(message)

    def sync_log_exceptions_decorator(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                self.log_exception(ex)

        return wrapper

    def log_exceptions_decorator(self, func):
        """Универсальный декоратор для логирования исключений."""
        
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as ex:
                async with self.async_lock:
                    self.log_exception(ex)

        return async_wrapper if inspect.iscoroutinefunction(func) else self.sync_log_exceptions_decorator(func)