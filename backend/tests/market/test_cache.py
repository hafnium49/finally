"""Tests for PriceCache."""

from app.market.cache import PriceCache


class TestPriceCache:
    """Unit tests for the PriceCache."""

    def test_update_and_get(self):
        """Test updating and getting a price."""
        cache = PriceCache()
        update = cache.update("AAPL", 190.50)
        assert update.ticker == "AAPL"
        assert update.price == 190.50
        assert cache.get("AAPL") == update

    def test_first_update_is_flat(self):
        """Test that the first update has flat direction."""
        cache = PriceCache()
        update = cache.update("AAPL", 190.50)
        assert update.direction == "flat"
        assert update.previous_price == 190.50

    def test_direction_up(self):
        """Test price update with upward direction."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        update = cache.update("AAPL", 191.00)
        assert update.direction == "up"
        assert update.change == 1.00

    def test_direction_down(self):
        """Test price update with downward direction."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        update = cache.update("AAPL", 189.00)
        assert update.direction == "down"
        assert update.change == -1.00

    def test_remove(self):
        """Test removing a ticker from cache."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        cache.remove("AAPL")
        assert cache.get("AAPL") is None

    def test_remove_nonexistent(self):
        """Test removing a ticker that doesn't exist."""
        cache = PriceCache()
        cache.remove("AAPL")  # Should not raise

    def test_get_all(self):
        """Test getting all prices."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        cache.update("GOOGL", 175.00)
        all_prices = cache.get_all()
        assert set(all_prices.keys()) == {"AAPL", "GOOGL"}

    def test_version_increments(self):
        """Test that version counter increments."""
        cache = PriceCache()
        v0 = cache.version
        cache.update("AAPL", 190.00)
        assert cache.version == v0 + 1
        cache.update("AAPL", 191.00)
        assert cache.version == v0 + 2

    def test_get_price_convenience(self):
        """Test the convenience get_price method."""
        cache = PriceCache()
        cache.update("AAPL", 190.50)
        assert cache.get_price("AAPL") == 190.50
        assert cache.get_price("NOPE") is None

    def test_len(self):
        """Test __len__ method."""
        cache = PriceCache()
        assert len(cache) == 0
        cache.update("AAPL", 190.00)
        assert len(cache) == 1
        cache.update("GOOGL", 175.00)
        assert len(cache) == 2

    def test_contains(self):
        """Test __contains__ method."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        assert "AAPL" in cache
        assert "GOOGL" not in cache

    def test_custom_timestamp(self):
        """Test updating with a custom timestamp."""
        cache = PriceCache()
        custom_ts = 1234567890.0
        update = cache.update("AAPL", 190.50, timestamp=custom_ts)
        assert update.timestamp == custom_ts

    def test_price_rounding(self):
        """Test that prices are rounded to 2 decimal places."""
        cache = PriceCache()
        update = cache.update("AAPL", 190.12345)
        assert update.price == 190.12

    def test_session_anchor_set_on_first_update(self):
        """Test that session anchor is recorded on first price update."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        assert cache.get_session_anchor("AAPL") == 190.00

    def test_session_anchor_not_changed_on_subsequent_updates(self):
        """Test that session anchor stays at the first price, not updated later."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        cache.update("AAPL", 200.00)
        cache.update("AAPL", 180.00)
        assert cache.get_session_anchor("AAPL") == 190.00

    def test_session_anchor_none_for_unknown_ticker(self):
        """Test that session anchor returns None for unknown tickers."""
        cache = PriceCache()
        assert cache.get_session_anchor("UNKNOWN") is None

    def test_session_change_pct_up(self):
        """Test session change percent when price is up."""
        cache = PriceCache()
        cache.update("AAPL", 100.00)
        cache.update("AAPL", 110.00)
        pct = cache.get_session_change_pct("AAPL")
        assert pct == 10.0

    def test_session_change_pct_down(self):
        """Test session change percent when price is down."""
        cache = PriceCache()
        cache.update("AAPL", 100.00)
        cache.update("AAPL", 90.00)
        pct = cache.get_session_change_pct("AAPL")
        assert pct == -10.0

    def test_session_change_pct_flat(self):
        """Test session change percent when price hasn't changed."""
        cache = PriceCache()
        cache.update("AAPL", 100.00)
        pct = cache.get_session_change_pct("AAPL")
        assert pct == 0.0

    def test_session_change_pct_none_for_unknown(self):
        """Test session change percent returns None for unknown ticker."""
        cache = PriceCache()
        assert cache.get_session_change_pct("UNKNOWN") is None

    def test_session_anchor_cleared_on_remove(self):
        """Test that removing a ticker clears its session anchor."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        cache.remove("AAPL")
        assert cache.get_session_anchor("AAPL") is None

    def test_session_anchor_reset_after_remove_and_readd(self):
        """Test that re-adding a removed ticker gets a fresh session anchor."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        cache.remove("AAPL")
        cache.update("AAPL", 200.00)  # Re-added at a new price
        assert cache.get_session_anchor("AAPL") == 200.00
