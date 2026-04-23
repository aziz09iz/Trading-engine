def funding_persistence(rates: list[float], threshold: float) -> int:
    if not rates:
        return 0

    latest = rates[-1]
    direction = 1 if latest > threshold else -1 if latest < -threshold else 0
    if direction == 0:
        return 0

    count = 0
    for rate in reversed(rates):
        if direction == 1 and rate > threshold:
            count += 1
        elif direction == -1 and rate < -threshold:
            count += 1
        else:
            break
    return count


def funding_momentum(rates: list[float], lookback: int = 3) -> float:
    if len(rates) <= lookback:
        return 0.0
    return rates[-1] - rates[-1 - lookback]
