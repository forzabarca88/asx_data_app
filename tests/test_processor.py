import sys
import os
import math
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_processor import (
    calculate_top_n_growth,
    prepare_trend_data,
    fetch_and_prepare_trend_data,
    clean_sentinel,
    clean_yield_sentinel,
    convert_excel_date,
    parse_income_statement,
    engineer_features,
)


def test_calculate_top_n_growth():
    """Test growth calculation with mock bulk snapshot data."""
    mock_df = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B", "C", "C"],
            "priceClose": [10.0, 15.0, 20.0, 18.0, 5.0, 10.0],
            "fetched_at": ["2024-01-01", "2024-06-01", "2024-01-01", "2024-06-01", "2024-01-01", "2024-06-01"],
        }
    )

    result = calculate_top_n_growth(mock_df, n=2)

    assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
    assert "growth_pct" in result.columns, "Missing growth_pct column"
    assert "start_value" in result.columns, "Missing start_value column"
    assert "end_value" in result.columns, "Missing end_value column"

    expected_growth_c = ((10.0 - 5.0) / 5.0) * 100  # 100%
    expected_growth_a = ((15.0 - 10.0) / 10.0) * 100  # 50%

    top_symbol = result.iloc[0]["symbol"]
    top_growth = result.iloc[0]["growth_pct"]

    assert top_symbol == "C", f"Expected top symbol 'C', got '{top_symbol}'"
    assert abs(top_growth - expected_growth_c) < 0.1, f"Expected growth ~{expected_growth_c}, got {top_growth}"

    second_symbol = result.iloc[1]["symbol"]
    second_growth = result.iloc[1]["growth_pct"]
    assert second_symbol == "A", f"Expected second symbol 'A', got '{second_symbol}'"
    assert abs(second_growth - expected_growth_a) < 0.1, f"Expected growth ~{expected_growth_a}, got {second_growth}"

    print("PASS: calculate_top_n_growth correctly calculates growth and sorts")


def test_prepare_trend_data():
    """Test trend data filtering with actual schema columns."""
    mock_df = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B"],
            "fetched_at": ["2024-06-01", "2024-12-01", "2024-03-01", "2024-09-01"],
            "priceClose": [10.0, 15.0, 20.0, 25.0],
        }
    )

    result = prepare_trend_data(mock_df, ["A"])

    assert len(result) == 2, f"Expected 2 rows for symbol A, got {len(result)}"
    assert all(result["symbol"] == "A"), "All rows should be symbol A"
    dates = pd.to_datetime(result["fetched_at"])
    assert list(dates) == sorted(dates), "Dates should be sorted chronologically"

    print("PASS: prepare_trend_data correctly filters and sorts")


def test_empty_dataframe():
    """Test handling of empty dataframes."""
    empty_df = pd.DataFrame(columns=["symbol", "priceClose", "fetched_at"])
    result = calculate_top_n_growth(empty_df, n=5)
    assert len(result) == 0, "Should return empty result for empty input"
    print("PASS: empty dataframe handled correctly")


def test_na_handling():
    """Test handling of missing values."""
    mock_df = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B"],
            "priceClose": [10.0, None, 20.0, 25.0],
            "fetched_at": ["2024-01-01", "2024-03-01", "2024-01-01", "2024-06-01"],
        }
    )

    result = calculate_top_n_growth(mock_df, n=10)
    assert not result.empty, "Should handle NA values without crashing"
    assert len(result) == 2, f"Expected 2 valid rows after NA filtering, got {len(result)}"
    print("PASS: NA values handled correctly")


def test_fetch_and_prepare_trend_data():
    """Test history fetching and combining for trend chart."""
    def mock_get_history(sym):
        dates = {
            "A": [("2024-01-01", 10.0), ("2024-06-01", 12.0)],
            "B": [("2024-01-01", 20.0), ("2024-06-01", 18.0)],
        }
        return pd.DataFrame(
            {"symbol": [sym] * 2, "fetched_at": [d[0] for d in dates[sym]], "priceClose": [d[1] for d in dates[sym]]},
        )

    result = fetch_and_prepare_trend_data(["A", "B"], mock_get_history)

    assert len(result) == 4, f"Expected 4 rows, got {len(result)}"
    assert set(result["symbol"].unique()) == {"A", "B"}, "Should contain both symbols"
    assert not result.empty, "Should not be empty"
    dates = pd.to_datetime(result["fetched_at"])
    assert list(dates) == sorted(dates), "Dates should be sorted chronologically"

    print("PASS: fetch_and_prepare_trend_data correctly fetches and combines histories")


def test_fetch_and_prepare_empty():
    """Test fetch_and_prepare_trend_data with empty symbols list."""
    result = fetch_and_prepare_trend_data([], lambda s: pd.DataFrame())
    assert result.empty, "Should return empty for empty symbol list"
    print("PASS: fetch_and_prepare_trend_data handles empty input")


# ── Feature Engineering Tests ──────────────────────────────────────


def test_clean_sentinel_pe():
    """Test P/E sentinel cleaning."""
    assert np.isnan(clean_sentinel(-99999.99))
    assert np.isnan(clean_sentinel(-100000))
    assert clean_sentinel(25.5) == 25.5
    assert clean_sentinel(1.0) == 1.0
    assert np.isnan(clean_sentinel(None))
    assert np.isnan(clean_sentinel(np.nan))
    print("PASS: clean_sentinel correctly handles P/E sentinels")


def test_clean_yield_sentinel():
    """Test FCF yield sentinel cleaning."""
    assert np.isnan(clean_yield_sentinel(-1.00000010000001e-05))
    assert clean_yield_sentinel(0.0573) == 0.0573
    assert clean_yield_sentinel(0.0) == 0.0
    assert np.isnan(clean_yield_sentinel(None))
    print("PASS: clean_yield_sentinel correctly handles yield sentinels")


def test_convert_excel_date():
    """Test Excel serial date conversion."""
    result = convert_excel_date(45838)
    expected = pd.Timestamp(2025, 6, 30)
    assert result == expected, f"Expected {expected}, got {result}"

    result2 = convert_excel_date(45531)
    expected2 = pd.Timestamp(2024, 8, 27)
    assert result2 == expected2, f"Expected {expected2}, got {result2}"

    assert pd.isna(convert_excel_date(None))
    assert pd.isna(convert_excel_date(np.nan))
    print("PASS: convert_excel_date correctly converts serial dates")


def test_parse_income_statement():
    """Test income statement parsing with single quotes."""
    stmt = "[{'revenue': 1071595000, 'netIncome': 79895000, 'period': '2025A'}, {'revenue': 867978000, 'netIncome': 3657000, 'period': '2024A'}]"
    result = parse_income_statement(stmt)
    assert len(result) == 2
    assert result[0]["period"] == "2024A"
    assert result[1]["period"] == "2025A"
    assert result[1]["revenue"] == 1071595000

    empty_result = parse_income_statement(None)
    assert empty_result == []

    empty_result2 = parse_income_statement("")
    assert empty_result2 == []
    print("PASS: parse_income_statement correctly parses and sorts statements")


def test_engineer_features_valuation():
    """Test valuation feature computation."""
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
    expected_mc = 1254722736 * 2.34
    assert abs(row["market_cap"] - expected_mc) < 1, f"Market cap: expected {expected_mc}, got {row['market_cap']}"
    assert abs(row["cleaned_pe"] - 28.50183) < 0.01
    assert abs(row["earnings_yield"] - (1 / 28.50183)) < 0.001
    assert abs(row["price_to_cash"] - 15.2) < 0.01
    assert abs(row["free_cash_flow_yield"] - 0.0573) < 0.001

    # Growth
    expected_yoy = (1071595000 - 867978000) / 867978000
    assert abs(row["yoy_revenue_growth"] - expected_yoy) < 0.01
    expected_margin = 79895000 / 1071595000
    assert abs(row["latest_net_margin"] - expected_margin) < 0.01
    expected_quality = 120000000 / 79895000
    assert abs(row["earnings_quality_ratio"] - expected_quality) < 0.01
    assert row["net_income_direction"] > 0

    # 3-Year CAGR
    expected_cagr = (1071595000 / 500000000) ** (1 / 3) - 1
    assert abs(row["revenue_cagr_3y"] - expected_cagr) < 0.01

    # Dividend
    assert abs(row["raw_dividend_yield"] - 0.035) < 0.001
    expected_franking = 1.0 + (80.0 / 100) * (0.30 / 0.70)
    assert abs(row["franking_credit_multiplier"] - expected_franking) < 0.001
    assert abs(row["grossed_up_yield"] - 0.035 * expected_franking) < 0.001
    assert abs(row["dividend_payout_ratio"] - 0.08 / 0.10) < 0.01
    assert row["dividend_currency_risk"] == False

    # Liquidity
    expected_spread = (2.38 - 2.37) / 2.34
    assert abs(row["bid_ask_spread_pct"] - expected_spread) < 0.001
    expected_range = (2.34 - 1.375) / (4.93 - 1.375)
    assert abs(row["range_position_52w"] - expected_range) < 0.01
    expected_turnover = 26340338.61 / 1254722736
    assert abs(row["volume_turnover_ratio"] - expected_turnover) < 0.001
    expected_intraday = (2.40 - 2.30) / 2.34
    assert abs(row["intraday_volatility"] - expected_intraday) < 0.001

    # Date
    assert row["period_end_date"] == pd.Timestamp(2025, 6, 30)

    print("PASS: engineer_features computes all features correctly")


def test_engineer_features_sentinels():
    """Test that sentinel values are properly cleaned."""
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

    result = engineer_features(df)
    row = result.iloc[0]

    assert np.isnan(row["cleaned_pe"]), "P/E sentinel should be NaN"
    assert np.isnan(row["earnings_yield"]), "Earnings yield should be NaN when P/E is NaN"
    assert np.isnan(row["price_to_cash"]), "P/C sentinel should be NaN"
    assert np.isnan(row["free_cash_flow_yield"]), "FCF yield sentinel should be NaN"
    assert row["franking_credit_multiplier"] == 1.0, "No franking should give multiplier of 1.0"
    assert pd.isna(row["period_end_date"]), "Null date should be NaT"

    print("PASS: engineer_features properly cleans sentinel values")


def test_engineer_features_fx_risk():
    """Test dividend currency risk flag for non-AUD dividends."""
    df = pd.DataFrame([{
        "symbol": "ZIM",
        "priceClose": 10.0,
        "priceAsk": 10.1,
        "priceBid": 9.9,
        "priceFiftyTwoWeekHigh": 15.0,
        "priceFiftyTwoWeekLow": 5.0,
        "priceDayHigh": 10.2,
        "priceDayLow": 9.8,
        "volumeAverage": 500000,
        "numOfShares": 100000000,
        "priceEarningsRatio": 12.0,
        "priceToCash": 8.0,
        "freeCashFlowYield": 0.04,
        "yieldAnnual": 0.05,
        "frankingPercent": None,
        "dividend": 0.50,
        "earningsPerShare": 0.80,
        "dividendCurrency": "USD",
        "incomeStatement": "",
        "fPeriodEndDate": None,
        "fetched_at": "2025-07-01",
    }])

    result = engineer_features(df)
    row = result.iloc[0]

    assert row["dividend_currency_risk"] == True, "USD dividend should flag FX risk"
    assert row["franking_credit_multiplier"] == 1.0, "No franking data gives multiplier of 1.0"

    print("PASS: dividend currency risk flag works correctly")


def test_engineer_features_empty():
    """Test engineer_features with empty DataFrame."""
    df = pd.DataFrame()
    result = engineer_features(df)
    assert result.empty, "Should return empty DataFrame for empty input"
    print("PASS: engineer_features handles empty DataFrame")


def test_engineer_features_multi_symbol():
    """Test engineer_features deduplicates to latest snapshot per symbol."""
    df = pd.DataFrame([
        {"symbol": "A", "priceClose": 10.0, "fetched_at": "2025-01-01", "numOfShares": 1000000},
        {"symbol": "A", "priceClose": 12.0, "fetched_at": "2025-06-01", "numOfShares": 1000000},
        {"symbol": "B", "priceClose": 20.0, "fetched_at": "2025-03-01", "numOfShares": 2000000},
    ])

    result = engineer_features(df)
    assert len(result) == 2, f"Expected 2 unique symbols, got {len(result)}"

    a_row = result[result["symbol"] == "A"].iloc[0]
    assert abs(a_row["market_cap"] - 12000000) < 1, "Should use latest snapshot for symbol A"

    b_row = result[result["symbol"] == "B"].iloc[0]
    assert abs(b_row["market_cap"] - 40000000) < 1, "Should preserve only data for symbol B"

    print("PASS: engineer_features correctly deduplicates to latest snapshot")


if __name__ == "__main__":
    tests = [
        test_calculate_top_n_growth,
        test_prepare_trend_data,
        test_empty_dataframe,
        test_na_handling,
        test_fetch_and_prepare_trend_data,
        test_fetch_and_prepare_empty,
        test_clean_sentinel_pe,
        test_clean_yield_sentinel,
        test_convert_excel_date,
        test_parse_income_statement,
        test_engineer_features_valuation,
        test_engineer_features_sentinels,
        test_engineer_features_fx_risk,
        test_engineer_features_empty,
        test_engineer_features_multi_symbol,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASS")
    else:
        print("SOME TESTS FAILED")