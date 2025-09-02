import asyncio
import pytest
from dotenv import load_dotenv

from src.models.kucoin_model import KucoinRawData
from src.services.extractors.kucoin_extractor import (
    KucoinExtractor,
    KucoinExtractorParams,
    KucoinWSData,
)


load_dotenv()


class TestKucoinWSData:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ws_bullet_data(self):
        result = await KucoinWSData.get_kucoin_ws_details()

        # Assertions
        assert isinstance(result, dict), "Expected a dict"
        assert "data" in result, "Missing data key"
        assert "instanceServers" in result["data"], "Missing instanceServers in data"
        assert isinstance(
            result["data"]["instanceServers"], list
        ), "instanceServers is not a list"
        assert "token" in result["data"], "Missing token"


class TestKucoinExtractorStream:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_kucoin_stream(self):
        extractor = KucoinExtractor()
        params = KucoinExtractorParams()
        results: list[KucoinRawData] = []

        async def run_extractor():
            async for result in extractor.extract_async(params):
                results.append(result)

        # Run extractor in background
        task = asyncio.create_task(run_extractor())

        # Sleep 1s for results to come in
        await asyncio.sleep(2)
        extractor.request_stop()

        # wait for stream to stop and clean up
        await task

        assert len(results) > 0, "No messages were streamed"
        assert isinstance(results[0], KucoinRawData), "Expected type KucoinRawData"
