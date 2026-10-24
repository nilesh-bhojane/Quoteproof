import pytest
from app.services.analytics import record_event, get_events, calculate_roi, clear_events, summary


class TestAnalyticsService:
    def setup_method(self):
        clear_events()

    def test_record_and_get_events(self):
        evt = record_event("quote-101", "draft_created", {"items": 3})
        assert evt["quote_id"] == "quote-101"
        assert evt["event_type"] == "draft_created"
        assert "timestamp" in evt

        events = get_events("quote-101")
        assert len(events) == 1
        assert events[0]["details"]["items"] == 3

    def test_calculate_roi_basic(self):
        # 10 minutes manual (600s), 4 minutes assisted (240s)
        res = calculate_roi(manual_seconds=600, assisted_seconds=240)
        assert res["time_saved_seconds"] == 360.0
        assert res["percentage_reduction"] == 60.0
        # No hourly rate provided -> labor value must be None
        assert res["estimated_labour_value_saved"] is None

    def test_calculate_roi_with_explicit_hourly_cost(self):
        # 1 hour manual (3600s), 30 min assisted (1800s) -> 1800s saved = 0.5 hours
        # Rate: 500 Rs/hr -> 250 Rs saved
        res = calculate_roi(manual_seconds=3600, assisted_seconds=1800, hourly_labour_cost=500)
        assert res["time_saved_seconds"] == 1800.0
        assert res["percentage_reduction"] == 50.0
        assert res["estimated_labour_value_saved"] == 250.0

    def test_calculate_roi_none_inputs(self):
        res = calculate_roi(manual_seconds=None, assisted_seconds=None)
        assert res["time_saved_seconds"] is None
        assert res["estimated_labour_value_saved"] is None

    def test_summary_returns_baseline(self):
        record_event("q-1", "draft_created")
        s = summary()
        assert s["quotes_tested"] == 1
        assert s["total_events_logged"] == 1
        assert s["estimated_labour_value_saved"] is None
