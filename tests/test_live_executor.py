from trading_system.execution.live_executor import format_price, round_size


def test_round_size_respects_asset_decimals() -> None:
    assert round_size(1.23456, 3) == 1.234


def test_format_price_respects_perp_precision_rules() -> None:
    assert format_price(1234.56, 1) == 1234.5
