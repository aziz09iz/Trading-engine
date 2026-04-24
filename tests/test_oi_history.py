from trading_system.features.oi_history import OpenInterestHistory


def test_oi_history_zscore_moves_positive(tmp_path) -> None:
    history = OpenInterestHistory(path=str(tmp_path / "oi.json"), window=10)
    for value in [100, 110, 105, 108, 112, 109]:
        history.push("BTC", value)

    zscore = history.push("BTC", 140)

    assert zscore > 1.0
