from enum import Enum


class Currency(Enum):
    USD = 0
    CAD = 1
    EUR = 2


def convert(pair, amount):
    print(pair)
    if pair == "USD/CAD":
        return int(round(amount * 1.33))
    elif pair == "CAD/USD":
        return int(round(amount * 0.75))
    elif pair == "USD/EUR":
        return int(round(amount * 0.88))
    elif pair == "EUR/USD":
        return int(round(amount * 1.14))
    elif pair == "CAD/EUR":
        return int(round(amount * 0.66))
    elif pair == "EUR/CAD":
        return int(round(amount * 1.51))
    else:
        raise ValueError("Invalid currency pair.")
