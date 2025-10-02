"""
Tests for date utility functions and NLP date range parsing.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from app.utils.date_utils import (
    get_month_range,
    get_quarter_range,
    get_year_range,
    parse_date_range,
)


class TestDateRangeHelpers:
    """Test suite for basic date range calculation helpers."""

    def test_get_month_range_january(self):
        """Test month range for January."""
        start, end = get_month_range(datetime(2025, 1, 15))
        assert start == "2025-01-01"
        assert end == "2025-01-31"

    def test_get_month_range_february_non_leap(self):
        """Test February in non-leap year."""
        start, end = get_month_range(datetime(2025, 2, 10))
        assert start == "2025-02-01"
        assert end == "2025-02-28"

    def test_get_month_range_february_leap_year(self):
        """Test February in leap year."""
        start, end = get_month_range(datetime(2024, 2, 10))
        assert start == "2024-02-01"
        assert end == "2024-02-29"

    def test_get_month_range_december(self):
        """Test month range for December."""
        start, end = get_month_range(datetime(2025, 12, 25))
        assert start == "2025-12-01"
        assert end == "2025-12-31"

    def test_get_month_range_30_day_month(self):
        """Test month with 30 days (September)."""
        start, end = get_month_range(datetime(2025, 9, 15))
        assert start == "2025-09-01"
        assert end == "2025-09-30"

    def test_get_month_range_31_day_month(self):
        """Test month with 31 days (October)."""
        start, end = get_month_range(datetime(2025, 10, 15))
        assert start == "2025-10-01"
        assert end == "2025-10-31"

    def test_get_quarter_range_q1(self):
        """Test Q1 range (Jan-Mar)."""
        start, end = get_quarter_range(2025, 1)
        assert start == "2025-01-01"
        assert end == "2025-03-31"

    def test_get_quarter_range_q2(self):
        """Test Q2 range (Apr-Jun)."""
        start, end = get_quarter_range(2025, 2)
        assert start == "2025-04-01"
        assert end == "2025-06-30"

    def test_get_quarter_range_q3(self):
        """Test Q3 range (Jul-Sep)."""
        start, end = get_quarter_range(2025, 3)
        assert start == "2025-07-01"
        assert end == "2025-09-30"

    def test_get_quarter_range_q4(self):
        """Test Q4 range (Oct-Dec)."""
        start, end = get_quarter_range(2025, 4)
        assert start == "2025-10-01"
        assert end == "2025-12-31"

    def test_get_quarter_range_invalid_quarter_too_low(self):
        """Test invalid quarter number (too low)."""
        with pytest.raises(ValueError, match="Quarter must be 1-4"):
            get_quarter_range(2025, 0)

    def test_get_quarter_range_invalid_quarter_too_high(self):
        """Test invalid quarter number (too high)."""
        with pytest.raises(ValueError, match="Quarter must be 1-4"):
            get_quarter_range(2025, 5)

    def test_get_year_range(self):
        """Test full year range."""
        start, end = get_year_range(2025)
        assert start == "2025-01-01"
        assert end == "2025-12-31"

    def test_get_year_range_different_year(self):
        """Test year range for different year."""
        start, end = get_year_range(2024)
        assert start == "2024-01-01"
        assert end == "2024-12-31"


class TestParseDateRangeRelativeMonth:
    """Test parsing of relative month expressions."""

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date for consistent testing (October 15, 2025)."""
        return datetime(2025, 10, 15)

    def test_parse_this_month(self, reference_date):
        """Test 'this month' parsing."""
        result = parse_date_range("this month", reference_date=reference_date)
        assert result["start_date"] == "2025-10-01"
        assert result["end_date"] == "2025-10-31"
        assert result["month"] == "2025-10"

    def test_parse_current_month(self, reference_date):
        """Test 'current month' parsing."""
        result = parse_date_range("current month", reference_date=reference_date)
        assert result["start_date"] == "2025-10-01"
        assert result["end_date"] == "2025-10-31"

    def test_parse_last_month(self, reference_date):
        """Test 'last month' parsing."""
        result = parse_date_range("last month", reference_date=reference_date)
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"
        assert result["month"] == "2025-09"

    def test_parse_previous_month(self, reference_date):
        """Test 'previous month' parsing."""
        result = parse_date_range("previous month", reference_date=reference_date)
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"

    def test_parse_next_month(self, reference_date):
        """Test 'next month' parsing."""
        result = parse_date_range("next month", reference_date=reference_date)
        assert result["start_date"] == "2025-11-01"
        assert result["end_date"] == "2025-11-30"

    def test_parse_months_ago(self, reference_date):
        """Test 'N months ago' parsing."""
        result = parse_date_range("2 months ago", reference_date=reference_date)
        assert result["start_date"] == "2025-08-01"
        assert result["end_date"] == "2025-08-31"
        assert result["month"] == "2025-08"

    def test_parse_one_month_ago(self, reference_date):
        """Test '1 month ago' (singular form)."""
        result = parse_date_range("1 month ago", reference_date=reference_date)
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"


class TestParseDateRangeLastNDays:
    """Test parsing of 'last N days' patterns."""

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date (October 15, 2025)."""
        return datetime(2025, 10, 15)

    def test_parse_last_30_days(self, reference_date):
        """Test 'last 30 days' parsing."""
        result = parse_date_range("last 30 days", reference_date=reference_date)
        assert result["start_date"] == "2025-09-16"  # 30 days back from Oct 15
        assert result["end_date"] == "2025-10-15"
        assert result["month"] is None

    def test_parse_last_7_days(self, reference_date):
        """Test 'last 7 days' parsing."""
        result = parse_date_range("last 7 days", reference_date=reference_date)
        assert result["start_date"] == "2025-10-09"
        assert result["end_date"] == "2025-10-15"

    def test_parse_past_90_days(self, reference_date):
        """Test 'past 90 days' parsing."""
        result = parse_date_range("past 90 days", reference_date=reference_date)
        # Oct 15 - 89 days = July 18 (90 days inclusive)
        assert result["start_date"] == "2025-07-18"
        assert result["end_date"] == "2025-10-15"

    def test_parse_previous_1_day(self, reference_date):
        """Test 'previous 1 day' (edge case)."""
        result = parse_date_range("previous 1 day", reference_date=reference_date)
        assert result["start_date"] == "2025-10-15"  # Same day (inclusive)
        assert result["end_date"] == "2025-10-15"


class TestParseDateRangeQuarters:
    """Test parsing of quarter expressions."""

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date (October 15, 2025 - Q4)."""
        return datetime(2025, 10, 15)

    def test_parse_this_quarter(self, reference_date):
        """Test 'this quarter' parsing (Q4)."""
        result = parse_date_range("this quarter", reference_date=reference_date)
        assert result["start_date"] == "2025-10-01"
        assert result["end_date"] == "2025-12-31"
        assert result["month"] is None

    def test_parse_current_quarter(self, reference_date):
        """Test 'current quarter' parsing."""
        result = parse_date_range("current quarter", reference_date=reference_date)
        assert result["start_date"] == "2025-10-01"
        assert result["end_date"] == "2025-12-31"

    def test_parse_last_quarter(self, reference_date):
        """Test 'last quarter' parsing (Q3)."""
        result = parse_date_range("last quarter", reference_date=reference_date)
        assert result["start_date"] == "2025-07-01"
        assert result["end_date"] == "2025-09-30"

    def test_parse_specific_q1_with_year(self, reference_date):
        """Test 'Q1 2025' parsing."""
        result = parse_date_range("Q1 2025", reference_date=reference_date)
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-03-31"

    def test_parse_specific_q3_with_year(self, reference_date):
        """Test 'Q3 2025' parsing."""
        result = parse_date_range("Q3 2025", reference_date=reference_date)
        assert result["start_date"] == "2025-07-01"
        assert result["end_date"] == "2025-09-30"

    def test_parse_quarter_without_year(self, reference_date):
        """Test 'Q2' without year (defaults to current year)."""
        result = parse_date_range("Q2", reference_date=reference_date)
        assert result["start_date"] == "2025-04-01"
        assert result["end_date"] == "2025-06-30"


class TestParseDateRangeYears:
    """Test parsing of year expressions."""

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date (October 15, 2025)."""
        return datetime(2025, 10, 15)

    def test_parse_this_year(self, reference_date):
        """Test 'this year' parsing."""
        result = parse_date_range("this year", reference_date=reference_date)
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-12-31"
        assert result["month"] is None

    def test_parse_current_year(self, reference_date):
        """Test 'current year' parsing."""
        result = parse_date_range("current year", reference_date=reference_date)
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-12-31"

    def test_parse_last_year(self, reference_date):
        """Test 'last year' parsing."""
        result = parse_date_range("last year", reference_date=reference_date)
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"

    def test_parse_specific_year(self, reference_date):
        """Test '2024' parsing."""
        result = parse_date_range("2024", reference_date=reference_date)
        assert result["start_date"] == "2024-01-01"
        assert result["end_date"] == "2024-12-31"


class TestParseDateRangeSpecificMonths:
    """Test parsing of specific month names."""

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date."""
        return datetime(2025, 10, 15)

    def test_parse_full_month_name(self, reference_date):
        """Test 'September 2025' parsing."""
        result = parse_date_range("September 2025", reference_date=reference_date)
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"
        assert result["month"] == "2025-09"

    def test_parse_abbreviated_month(self, reference_date):
        """Test 'Sep 2025' parsing."""
        result = parse_date_range("Sep 2025", reference_date=reference_date)
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"

    def test_parse_month_with_comma(self, reference_date):
        """Test 'January, 2025' parsing."""
        result = parse_date_range("January, 2025", reference_date=reference_date)
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-01-31"

    def test_parse_iso_month_format(self, reference_date):
        """Test '2025-09' ISO format parsing."""
        result = parse_date_range("2025-09", reference_date=reference_date)
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"
        assert result["month"] == "2025-09"

    def test_parse_december(self, reference_date):
        """Test December parsing (edge case for month-end)."""
        result = parse_date_range("December 2024", reference_date=reference_date)
        assert result["start_date"] == "2024-12-01"
        assert result["end_date"] == "2024-12-31"


class TestParseDateRangeEdgeCases:
    """Test edge cases and year boundary transitions."""

    def test_december_to_january_next_month(self):
        """Test 'next month' when current month is December."""
        reference_date = datetime(2025, 12, 15)
        result = parse_date_range("next month", reference_date=reference_date)
        assert result["start_date"] == "2026-01-01"
        assert result["end_date"] == "2026-01-31"

    def test_january_to_december_last_month(self):
        """Test 'last month' when current month is January."""
        reference_date = datetime(2025, 1, 15)
        result = parse_date_range("last month", reference_date=reference_date)
        assert result["start_date"] == "2024-12-01"
        assert result["end_date"] == "2024-12-31"

    def test_q1_to_q4_last_quarter(self):
        """Test 'last quarter' when current quarter is Q1."""
        reference_date = datetime(2025, 1, 15)  # Q1
        result = parse_date_range("last quarter", reference_date=reference_date)
        assert result["start_date"] == "2024-10-01"
        assert result["end_date"] == "2024-12-31"

    def test_case_insensitivity(self):
        """Test that parsing is case-insensitive."""
        reference_date = datetime(2025, 10, 15)
        result1 = parse_date_range("LAST MONTH", reference_date=reference_date)
        result2 = parse_date_range("Last Month", reference_date=reference_date)
        result3 = parse_date_range("last month", reference_date=reference_date)

        assert result1 == result2 == result3

    def test_unrecognized_pattern_defaults_to_current_month(self):
        """Test that unrecognized patterns default to current month."""
        reference_date = datetime(2025, 10, 15)
        result = parse_date_range("some random gibberish", reference_date=reference_date)
        assert result["start_date"] == "2025-10-01"
        assert result["end_date"] == "2025-10-31"
        assert result["month"] == "2025-10"


class TestParseDateRangeInSentences:
    """Test extracting date ranges from natural language sentences."""

    @pytest.fixture
    def reference_date(self):
        """Fixed reference date."""
        return datetime(2025, 10, 15)

    def test_parse_from_sentence(self, reference_date):
        """Test extracting 'September 2025' from a full sentence."""
        result = parse_date_range(
            "Show me my spending for September 2025",
            reference_date=reference_date
        )
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"

    def test_parse_last_month_from_sentence(self, reference_date):
        """Test extracting 'last month' from sentence."""
        result = parse_date_range(
            "I want to see last month's transactions",
            reference_date=reference_date
        )
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"

    def test_parse_q3_from_sentence(self, reference_date):
        """Test extracting 'Q3 2025' from sentence."""
        result = parse_date_range(
            "Analyze my Q3 2025 spending patterns",
            reference_date=reference_date
        )
        assert result["start_date"] == "2025-07-01"
        assert result["end_date"] == "2025-09-30"


class TestParseDateRangeLLMFallback:
    """Test LLM fallback for complex expressions."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        llm = Mock()
        response = Mock()
        response.content = '{"start_date": "2025-01-01", "end_date": "2025-03-31", "month": null}'
        llm.invoke.return_value = response
        return llm

    def test_llm_fallback_called_for_complex_expression(self, mock_llm):
        """Test that LLM is called for complex expressions not matching rules."""
        reference_date = datetime(2025, 10, 15)
        # Use truly complex expression that won't match any rule-based pattern
        result = parse_date_range(
            "between Christmas and New Year",
            llm=mock_llm,
            reference_date=reference_date
        )

        # Should call LLM since rule-based parsing won't match this
        assert mock_llm.invoke.called
        assert result["start_date"] == "2025-01-01"
        assert result["end_date"] == "2025-03-31"

    def test_llm_not_called_for_simple_expression(self, mock_llm):
        """Test that LLM is NOT called for simple rule-based patterns."""
        reference_date = datetime(2025, 10, 15)
        result = parse_date_range(
            "last month",
            llm=mock_llm,
            reference_date=reference_date
        )

        # Should NOT call LLM (rule-based parsing handles this)
        assert not mock_llm.invoke.called
        assert result["start_date"] == "2025-09-01"
        assert result["end_date"] == "2025-09-30"

    def test_llm_fallback_error_handling(self):
        """Test graceful fallback when LLM fails."""
        llm = Mock()
        llm.invoke.side_effect = Exception("LLM error")

        reference_date = datetime(2025, 10, 15)
        result = parse_date_range(
            "some complex expression",
            llm=llm,
            reference_date=reference_date
        )

        # Should default to current month when LLM fails
        assert result["start_date"] == "2025-10-01"
        assert result["end_date"] == "2025-10-31"

    def test_no_llm_provided_defaults_to_current_month(self):
        """Test that without LLM, complex expressions default to current month."""
        reference_date = datetime(2025, 10, 15)
        result = parse_date_range(
            "from January to March",  # Complex expression
            llm=None,
            reference_date=reference_date
        )

        # Should default to current month (no LLM available)
        assert result["start_date"] == "2025-10-01"
        assert result["end_date"] == "2025-10-31"
