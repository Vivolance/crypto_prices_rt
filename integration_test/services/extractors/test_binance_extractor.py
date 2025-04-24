
from src.services.extractors.binance_extractor import (
    BinanceExtractorParams,
    BinanceExtractor,
)
import asyncio
import pytest
from src.models.binance_model import BinanceRawData


class TestBinanceExtractorStream:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_extractor_stream(self):
        extractor = BinanceExtractor()
        params = BinanceExtractorParams()
        results: list[list[BinanceRawData]] = []

        async def run_extractor():
            async for result in extractor.extract_async(params):
                results.append(result)

        # Run extractor in the background
        task = asyncio.create_task(run_extractor())

        # Let it run briefly, then trigger the stop event
        await asyncio.sleep(2)
        extractor.request_stop()

        # Wait for the stream to stop and clean up
        try:
            await task
        except Exception as e:
            # Detect Binance’s 451 block
            if "451" in str(e):
                pytest.skip(f"CI runner IP blocked by Binance (451): {e}")
            # If it’s some other unexpected error, fail
            raise

        assert len(results) > 0, "No messages were streamed"
        # use pytest -s in CLI to return stdout
        print(results[0][0])
        assert isinstance(results[0], list), "Expected a list of BinanceRawData"
        assert isinstance(
            results[0][0], BinanceRawData
        ), "Parsed item is not of type BinanceRawData"
