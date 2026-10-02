"""Получение курсов валют из ExchangeRate-API (бесплатный тариф)."""

import httpx

# Бесплатный адрес, ключ не нужен. Курсы обновляются раз в сутки.
API_URL = "https://open.er-api.com/v6/latest/{base}"

# Не даём медленному или зависшему API «заморозить» бота.
REQUEST_TIMEOUT = 10  # секунд


class RateError(Exception):
    """Ошибка: не удалось получить курс валюты.

    Текст ошибки понятен пользователю, поэтому бот может показать его как есть.
    """


async def get_rate(base: str, target: str) -> float:
    """Возвращает, сколько единиц валюты `target` стоит 1 единица `base`.

    Пример: get_rate("USD", "RUB") -> 83.69

    Выбрасывает:
        RateError: если сервис недоступен или код валюты неизвестен.
    """
    # API ждёт коды заглавными буквами, а пользователь может написать "usd".
    base = base.upper()
    target = target.upper()

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(API_URL.format(base=base))
        data = response.json()
    except (httpx.HTTPError, ValueError) as e:
        # HTTPError — проблемы с сетью или истёк таймаут.
        # ValueError — в ответе пришёл не JSON.
        # `from e` сохраняет исходную ошибку, чтобы было видно причину при отладке.
        raise RateError("Сервис курсов валют сейчас недоступен") from e

    # Об ошибках API сообщает внутри JSON, например:
    # {"result": "error", "error-type": "unsupported-code"}
    if data.get("result") != "success":
        if data.get("error-type") == "unsupported-code":
            raise RateError(f"Неизвестная валюта: {base}")
        raise RateError("Сервис курсов валют вернул ошибку")

    # .get() вернёт None, если такой валюты нет, вместо падения с KeyError.
    rate = data["rates"].get(target)
    if rate is None:
        raise RateError(f"Неизвестная валюта: {target}")

    return rate


if __name__ == "__main__":
    # Быстрая ручная проверка: запусти `python rates.py`.
    # При импорте модуля в бота этот блок не выполняется.
    import asyncio

    print(asyncio.run(get_rate("USD", "RUB")))