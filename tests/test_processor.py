import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_processor import (
    calculate_top_n_growth,
    fetch_and_prepare_trend_data,
    engineer_features,
    detect_available_factors,
)


# ── Growth Ranking Tests ───────────────────────────────────────────


def test_calculate_top_n_growth():
    """Growth calculation produces correct percentages and sorting."""
    mock_df = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B", "C", "C"],
            "priceClose": [10.0, 15.0, 20.0, 18.0, 5.0, 10.0],
            "fetched_at": ["2024-01-01", "2024-06-01", "2024-01-01", "2024-06-01", "2024-01-01", "2024-06-01"],
        }
    )

    result = calculate_top_n_growth(mock_df, n=2)

    assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
    assert result.iloc[0]["symbol"] == "C", "Top grower should be C (+100%)"
    assert abs(result.iloc[0]["growth_pct"] - 100.0) < 0.1
    assert result.iloc[1]["symbol"] == "A", "Second grower should be A (+50%)"
    assert abs(result.iloc[1]["growth_pct"] - 50.0) < 0.1
    print("PASS: growth calculation and sorting correct")


def test_growth_empty_and_na():
    """Growth handles empty input and missing values gracefully."""
    empty_df = pd.DataFrame(columns=["symbol", "priceClose", "fetched_at"])
    assert calculate_top_n_growth(empty_df, n=5).empty

    na_df = pd.DataFrame({
        "symbol": ["A", "A", "B", "B"],
        "priceClose": [10.0, None, 20.0, 25.0],
        "fetched_at": ["2024-01-01", "2024-03-01", "2024-01-01", "2024-06-01"],
    })
    result = calculate_top_n_growth(na_df, n=10)
    assert len(result) == 2, "Should skip NA rows and still compute valid results"
    print("PASS: empty and NA handling correct")


# ── Trend Data Tests ───────────────────────────────────────────────


def test_fetch_and_prepare_trend_data():
    """Multi-symbol history fetching combines data and reports failures."""
    def mock_get_history(sym, **kwargs):
        data = {
            "A": [("2024-01-01", 10.0), ("2024-06-01", 12.0)],
            "B": [("2024-01-01", 20.0), ("2024-06-01", 18.0)],
        }
        return pd.DataFrame(
            {"symbol": [sym] * 2, "fetched_at": [d[0] for d in data[sym]], "priceClose": [d[1] for d in data[sym]]},
        )

    result, failed = fetch_and_prepare_trend_data(["A", "B"], mock_get_history)
    assert len(result) == 4
    assert set(result["symbol"].unique()) == {"A", "B"}
    assert failed == []
    dates = pd.to_datetime(result["fetched_at"])
    assert list(dates) == sorted(dates)
    print("PASS: multi-symbol history fetching correct")


def test_fetch_and_prepare_empty():
    """Empty symbol list returns empty result without error."""
    result, failed = fetch_and_prepare_trend_data([], lambda s, **kwargs: pd.DataFrame())
    assert result.empty
    assert failed == []
    print("PASS: empty input handled correctly")


# ── Feature Engineering Tests ──────────────────────────────────────


def test_engineer_features_full():
    """Full feature pipeline computes all metrics correctly."""
    df = pd.DataFrame([{
        "symbol": "ZIP",
        "priceClose": 2.34,
        "priceAsk": 2.38,
        "priceBid": 2.37,
        "priceFiftyTwoWeekHigh": 4.93,
        "priceFiftyTwoWeekLow": 1.375,
        "priceDayHigh": 2.40,
        "priceDayLow": 2.30,
        "volumeAverage": 26340338.61,
        "numOfShares": 1254722736,
        "priceEarningsRatio": 28.50183,
        "priceToCash": 15.2,
        "freeCashFlowYield": 0.0573,
        "yieldAnnual": 0.035,
        "frankingPercent": 80.0,
        "dividend": 0.08,
        "earningsPerShare": 0.10,
        "dividendCurrency": "AUD",
        "incomeStatement": "[{'revenue': 1071595000, 'netIncome': 79895000, 'cashFlow': 120000000, 'period': '2025A'}, {'revenue': 867978000, 'netIncome': 3657000, 'cashFlow': 50000000, 'period': '2024A'}, {'revenue': 677209000, 'netIncome': -377015000, 'cashFlow': -100000000, 'period': '2023A'}, {'revenue': 500000000, 'netIncome': -200000000, 'cashFlow': -50000000, 'period': '2022A'}]",
        "fPeriodEndDate": 45838,
        "fetched_at": "2025-07-01",
    }])

    result = engineer_features(df)
    assert len(result) == 1
    row = result.iloc[0]

    # Valuation
    assert abs(row["market_cap"] - 1254722736 * 2.34) < 1
    assert abs(row["cleaned_pe"] - 28.50183) < 0.01
    assert abs(row["earnings_yield"] - (1 / 28.50183)) < 0.001
    assert abs(row["price_to_cash"] - 15.2) < 0.01
    assert abs(row["free_cash_flow_yield"] - 0.0573) < 0.001

    # Growth
    assert abs(row["yoy_revenue_growth"] - (1071595000 - 867978000) / 867978000) < 0.01
    assert abs(row["latest_net_margin"] - 79895000 / 1071595000) < 0.01
    assert abs(row["earnings_quality_ratio"] - 120000000 / 79895000) < 0.01
    assert row["net_income_direction"] > 0
    assert abs(row["revenue_cagr_3y"] - ((1071595000 / 500000000) ** (1 / 3) - 1)) < 0.01

    # Dividend
    assert abs(row["raw_dividend_yield"] - 0.035) < 0.001
    expected_franking = 1.0 + (80.0 / 100) * (0.30 / 0.70)
    assert abs(row["franking_credit_multiplier"] - expected_franking) < 0.001
    assert abs(row["grossed_up_yield"] - 0.035 * expected_franking) < 0.001
    assert abs(row["dividend_payout_ratio"] - 0.8) < 0.01
    assert row["dividend_currency_risk"] == False

    # Liquidity
    assert abs(row["bid_ask_spread_pct"] - (2.38 - 2.37) / 2.34) < 0.001
    assert abs(row["range_position_52w"] - (2.34 - 1.375) / (4.93 - 1.375)) < 0.01
    assert abs(row["volume_turnover_ratio"] - 26340338.61 / 1254722736) < 0.001
    assert abs(row["intraday_volatility"] - (2.40 - 2.30) / 2.34) < 0.001

    # Date
    assert row["period_end_date"] == pd.Timestamp(2025, 6, 30)

    print("PASS: all features computed correctly")


def test_engineer_features_sentinels():
    """Sentinel values are cleaned to NaN; missing data degrades gracefully."""
    df = pd.DataFrame([{
        "symbol": "LOSS",
        "priceClose": 1.50,
        "priceAsk": 1.52,
        "priceBid": 1.48,
        "priceFiftyTwoWeekHigh": 3.00,
        "priceFiftyTwoWeekLow": 0.50,
        "priceDayHigh": 1.55,
        "priceDayLow": 1.45,
        "volumeAverage": 1000000,
        "numOfShares": 50000000,
        "priceEarningsRatio": -99999.99,
        "priceToCash": -99999.99,
        "freeCashFlowYield": -1.00000010000001e-05,
        "yieldAnnual": 0.0,
        "frankingPercent": None,
        "dividend": 0.0,
        "earningsPerShare": -0.05,
        "dividendCurrency": "AUD",
        "incomeStatement": "",
        "fPeriodEndDate": None,
        "fetched_at": "2025-07-01",
    }])

    result = engineer_features(df).iloc[0]
    assert np.isnan(result["cleaned_pe"]), "P/E sentinel should be NaN"
    assert np.isnan(result["earnings_yield"]), "Earnings yield NaN when P/E is NaN"
    assert np.isnan(result["price_to_cash"])
    assert np.isnan(result["free_cash_flow_yield"])
    assert result["franking_credit_multiplier"] == 1.0
    assert pd.isna(result["period_end_date"])
    print("PASS: sentinels cleaned, missing data handled")


def test_engineer_features_fx_risk():
    """Non-AUD dividends are flagged as FX risk."""
    df = pd.DataFrame([{
        "symbol": "ZIM",
        "priceClose": 10.0, "priceAsk": 10.1, "priceBid": 9.9,
        "priceFiftyTwoWeekHigh": 15.0, "priceFiftyTwoWeekLow": 5.0,
        "priceDayHigh": 10.2, "priceDayLow": 9.8,
        "volumeAverage": 500000, "numOfShares": 100000000,
        "priceEarningsRatio": 12.0, "priceToCash": 8.0,
        "freeCashFlowYield": 0.04, "yieldAnnual": 0.05,
        "frankingPercent": None, "dividend": 0.50,
        "earningsPerShare": 0.80, "dividendCurrency": "USD",
        "incomeStatement": "", "fPeriodEndDate": None, "fetched_at": "2025-07-01",
    }])

    row = engineer_features(df).iloc[0]
    assert row["dividend_currency_risk"] == True, "USD dividend should flag FX risk"
    assert row["franking_credit_multiplier"] == 1.0
    print("PASS: FX risk detection correct")


def test_engineer_features_empty():
    """Empty input returns empty result."""
    assert engineer_features(pd.DataFrame()).empty
    print("PASS: empty input handled")


def test_engineer_features_dedup():
    """Keeps only the latest snapshot per symbol."""
    df = pd.DataFrame([
        {"symbol": "A", "priceClose": 10.0, "fetched_at": "2025-01-01", "numOfShares": 1000000},
        {"symbol": "A", "priceClose": 12.0, "fetched_at": "2025-06-01", "numOfShares": 1000000},
        {"symbol": "B", "priceClose": 20.0, "fetched_at": "2025-03-01", "numOfShares": 2000000},
    ])
    result = engineer_features(df)
    assert len(result) == 2
    assert abs(result[result["symbol"] == "A"].iloc[0]["market_cap"] - 12000000) < 1
    assert abs(result[result["symbol"] == "B"].iloc[0]["market_cap"] - 40000000) < 1
    print("PASS: deduplication to latest snapshot correct")


# ── Available Factors ──────────────────────────────────────────────


def test_detect_available_factors():
    """Returns all numeric columns for user to choose from."""
    df = pd.DataFrame({
        "priceClose": [10.0], "volume": [1000],
        "numOfShares": [1000000], "yieldAnnual": [0.05],
        "symbol": ["A"], "name": ["Test"],
    })
    factors = detect_available_factors(df)
    assert set(factors) == {"priceClose", "volume", "numOfShares", "yieldAnnual"}
    assert "symbol" not in factors
    assert "name" not in factors
    print(f"PASS: returns all numeric columns: {factors}")


if __name__ == "__main__":
    tests = [
        test_calculate_top_n_growth,
        test_growth_empty_and_na,
        test_fetch_and_prepare_trend_data,
        test_fetch_and_prepare_empty,
        test_engineer_features_full,
        test_engineer_features_sentinels,
        test_engineer_features_fx_risk,
        test_engineer_features_empty,
        test_engineer_features_dedup,
        test_detect_available_factors,
    ]

    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    print("ALL TESTS PASS" if failed == 0 else "SOME TESTS FAILED")
