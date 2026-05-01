from trading_system.data.universe import UniverseMetrics, select_top_liquid_markets


def test_selects_top_ten_liquid_markets() -> None:
    markets = [
        UniverseMetrics(
            symbol=f"ASSET{i}",
            volume_24h=1_000_000_000 - i * 10_000_000,
            top_of_book_depth_usd=20_000_000 - i * 100_000,
            spread_bps=1 + (i % 3),
            open_interest_usd=500_000_000 - i * 1_000_000,
        )
        for i in range(12)
    ]

    selected = select_top_liquid_markets(markets)

    assert len(selected) == 10
    assert selected[0].symbol == "ASSET0"


def test_falls_back_when_spread_filter_removes_all_markets() -> None:
    markets = [
        UniverseMetrics(
            symbol=f"ASSET{i}",
            volume_24h=100_000_000 - i * 1_000_000,
            top_of_book_depth_usd=10_000_000,
            spread_bps=10.0,
            open_interest_usd=50_000_000,
        )
        for i in range(3)
    ]

    selected = select_top_liquid_markets(markets, limit=2, max_spread_bps=8.0)

    assert [market.symbol for market in selected] == ["ASSET0", "ASSET1"]
