def simple_moving_average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def trend_bias(ma_fast: float, ma_slow: float, mid_price: float) -> float:
    if ma_slow <= 0 or mid_price <= 0:
        return 0.0
    return max(-1.0, min(1.0, ((ma_fast - ma_slow) / mid_price) * 20.0))


def atr_percent(atr: float, mid_price: float) -> float:
    if mid_price <= 0:
        return 0.0
    return atr / mid_price
