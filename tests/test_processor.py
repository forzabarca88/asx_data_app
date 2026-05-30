import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_processor import calculate_top_n_growth, prepare_trend_data, fetch_and_prepare_trend_data


def test_calculate_top_n_growth():
    """Test 52-week growth calculation with mock bulk snapshot data."""
    mock_df = pd.DataFrame(
        {
            "symbol": ["A", "B", "C"],
            "priceClose": [15.0, 18.0, 10.0],
            "priceFiftyTwoWeekLow": [10.0, 20.0, 5.0],
        }
    )

    result = calculate_top_n_growth(mock_df, n=2)

    assert len(result) == 2, f"Expected 2 rows, got {len(result)}"
    assert "growth_pct" in result.columns, "Missing growth_pct column"
    assert "low_52w" in result.columns, "Missing low_52w column"
    assert "current_price" in result.columns, "Missing current_price column"

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

    print("PASS: calculate_top_n_growth correctly calculates 52-week growth and sorts")
    return True


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
    return True


def test_empty_dataframe():
    """Test handling of empty dataframes."""
    empty_df = pd.DataFrame(columns=["symbol", "priceClose", "priceFiftyTwoWeekLow"])
    result = calculate_top_n_growth(empty_df, n=5)
    assert len(result) == 0, "Should return empty result for empty input"
    print("PASS: empty dataframe handled correctly")
    return True


def test_na_handling():
    """Test handling of missing values."""
    mock_df = pd.DataFrame(
        {
            "symbol": ["A", "A", "B", "B"],
            "priceClose": [15.0, None, 18.0, 25.0],
            "priceFiftyTwoWeekLow": [10.0, 10.0, None, 20.0],
        }
    )

    result = calculate_top_n_growth(mock_df, n=10)
    assert not result.empty, "Should handle NA values without crashing"
    assert len(result) == 2, f"Expected 2 valid rows after NA filtering, got {len(result)}"
    assert result.iloc[0]["symbol"] == "A", "Expected symbol A as top growth"
    print("PASS: NA values handled correctly")
    return True


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
    return True


def test_fetch_and_prepare_empty():
    """Test fetch_and_prepare_trend_data with empty symbols list."""
    result = fetch_and_prepare_trend_data([], lambda s: pd.DataFrame())
    assert result.empty, "Should return empty for empty symbol list"
    print("PASS: fetch_and_prepare_trend_data handles empty input")
    return True


if __name__ == "__main__":
    all_passed = True
    all_passed &= test_calculate_top_n_growth()
    all_passed &= test_prepare_trend_data()
    all_passed &= test_empty_dataframe()
    all_passed &= test_na_handling()
    all_passed &= test_fetch_and_prepare_trend_data()
    all_passed &= test_fetch_and_prepare_empty()

    if all_passed:
        print("\nPhase 3 validation: ALL PASS")
    else:
        print("\nPhase 3 validation: SOME FAILURES")