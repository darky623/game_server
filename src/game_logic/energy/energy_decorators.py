from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException

from config.deps import get_services


def require_energy(energy_amount: int):
    """
    Декоратор для проверки и списания энергии перед выполнением действия.
    
    Args:
        energy_amount (int): Количество энергии, которое требуется для выполнения действия
    
    Raises:
        HTTPException: если недостаточно энергии или произошла ошибка при списании
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем текущего пользователя из параметров функции
            current_user = kwargs.get('current_user')
            if not current_user:
                for arg in args:
                    if hasattr(arg, 'id'):  # Ищем объект пользователя в позиционных аргументах
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=400,
                    detail="User not found in function parameters"
                )

            # Получаем сервисы
            services = kwargs.get('services')
            if not services:
                for arg in args:
                    if hasattr(arg, 'energy_service'):
                        services = arg
                        break
            
            if not services:
                # Если сервисы не найдены в аргументах, пробуем получить их через зависимости
                services = await get_services()

            # Проверяем и списываем энергию
            energy_result = await services.energy_service.update_energy(
                current_user.id,
                -energy_amount  # Отрицательное значение для списания
            )

            # Проверяем результат обновления энергии
            if isinstance(energy_result, dict):
                status_code = energy_result.get('status_code', 400)
                message = energy_result.get('message') or energy_result.get('detail', f"Insufficient energy."
                                                                                      f" Required: {energy_amount}")
                raise HTTPException(status_code=status_code, detail=message)

            # Выполняем основную функцию
            result = await func(*args, **kwargs)
            return result

        return wrapper
    return decorator
