"""Parametrized conformance tests for the MarketDataSource ABC.

Both concrete implementations (SimulatorDataSource, MassiveDataSource) must
support the same lifecycle: start → add_ticker → remove_ticker → stop, plus
get_tickers() at any point. These tests run the full sequence on each one to
catch any drift between implementations.
"""

from unittest.mock import patch

import pytest

from app.market.cache import PriceCache
from app.market.interface import MarketDataSource
from app.market.massive_client import MassiveDataSource
from app.market.simulator import SimulatorDataSource


def _build_simulator() -> tuple[MarketDataSource, PriceCache]:
    cache = PriceCache()
    source = SimulatorDataSource(price_cache=cache, update_interval=0.05)
    return source, cache


def _build_massive() -> tuple[MarketDataSource, PriceCache]:
    cache = PriceCache()
    source = MassiveDataSource(api_key="test-key", price_cache=cache, poll_interval=60.0)
    return source, cache


@pytest.fixture(params=["simulator", "massive"])
def source_and_cache(request):
    """Build each implementation in turn and yield (source, cache)."""
    builders = {"simulator": _build_simulator, "massive": _build_massive}
    source, cache = builders[request.param]()
    yield source, cache


@pytest.mark.asyncio
class TestMarketDataSourceConformance:
    """Each concrete implementation must honor the ABC contract."""

    async def test_is_subclass_of_abc(self, source_and_cache):
        source, _ = source_and_cache
        assert isinstance(source, MarketDataSource)

    async def test_get_tickers_before_start_is_empty(self, source_and_cache):
        source, _ = source_and_cache
        assert source.get_tickers() == []

    async def test_lifecycle(self, source_and_cache):
        source, cache = source_and_cache

        # Use a stub fetch for Massive so start()'s immediate poll doesn't hit the network.
        with patch("app.market.massive_client.RESTClient"):
            if isinstance(source, MassiveDataSource):
                stub = patch.object(source, "_fetch_snapshots", return_value=[])
            else:
                stub = patch.object(source, "_cache", cache)  # no-op patch for simulator

            with stub:
                await source.start(["AAPL", "GOOGL"])
                assert set(source.get_tickers()) == {"AAPL", "GOOGL"}

                await source.add_ticker("TSLA")
                assert "TSLA" in source.get_tickers()

                await source.remove_ticker("GOOGL")
                assert "GOOGL" not in source.get_tickers()

                await source.stop()
                # stop() must be idempotent.
                await source.stop()

    async def test_add_remove_are_async_callables(self, source_and_cache):
        """Both methods must be awaitable coroutines, not sync functions."""
        import inspect

        source, _ = source_and_cache
        assert inspect.iscoroutinefunction(source.add_ticker)
        assert inspect.iscoroutinefunction(source.remove_ticker)
        assert inspect.iscoroutinefunction(source.start)
        assert inspect.iscoroutinefunction(source.stop)
