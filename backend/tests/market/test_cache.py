"""Tests for PriceCache."""

import threading

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

    def test_version_does_not_bump_on_identical_price(self):
        """PLAN.md §6: SSE should be push-on-change, not push-on-tick."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        v1 = cache.version
        cache.update("AAPL", 190.00)  # identical price → no version bump
        assert cache.version == v1

    def test_version_does_not_bump_on_sub_cent_no_op(self):
        """Sub-cent moves that round to the same value should not bump version."""
        cache = PriceCache()
        cache.update("AAPL", 190.001)  # rounds to 190.00
        v1 = cache.version
        cache.update("AAPL", 190.002)  # still rounds to 190.00
        assert cache.version == v1

    def test_first_update_bumps_version(self):
        """The first update for a ticker must bump the version (seed event)."""
        cache = PriceCache()
        v0 = cache.version
        cache.update("AAPL", 190.00)
        assert cache.version == v0 + 1

    def test_remove_does_not_bump_version(self):
        """Removal is a silent op; SSE doesn't get an explicit "removed" frame."""
        cache = PriceCache()
        cache.update("AAPL", 190.00)
        v1 = cache.version
        cache.remove("AAPL")
        assert cache.version == v1

    def test_timestamp_zero_is_preserved(self):
        """timestamp=0.0 is a valid value (epoch) and must NOT be replaced."""
        cache = PriceCache()
        update = cache.update("AAPL", 190.50, timestamp=0.0)
        assert update.timestamp == 0.0

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

    def test_concurrent_updates_do_not_corrupt_cache(self):
        """Threadsafety smoke test: many threads can update() concurrently."""
        cache = PriceCache()
        n_threads = 4
        per_thread = 500

        def hammer(thread_id: int) -> None:
            for i in range(per_thread):
                # Distinct prices per (thread_id, i) so every call is a real change.
                cache.update("AAPL", 100.00 + thread_id * 1000 + i)

        threads = [threading.Thread(target=hammer, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Every update is a real change → version should equal total updates.
        assert cache.version == n_threads * per_thread
        # Cache must have a valid PriceUpdate for AAPL (no exceptions, no torn state).
        update = cache.get("AAPL")
        assert update is not None
        assert update.ticker == "AAPL"
        assert update.price > 0
