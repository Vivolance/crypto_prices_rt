"""
All extractors extend this base extractor class
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, AsyncGenerator, Any

import aiohttp
import asyncio
from aiohttp import ClientWebSocketResponse, WSMessage
from pydantic import BaseModel

from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)

# Create arbitrary typed variable that must implement from a BaseModel
# Such as RawPrices
ExtractorParams = TypeVar("ExtractorParams", bound=BaseModel)
ExtractedModel = TypeVar("ExtractedModel", bound=BaseModel)


class AsyncExtractor(ABC, Generic[ExtractorParams, ExtractedModel]):
    """
    Generic extractor takes in ExtractorParams and returns an ExtractedModel
    """

    @staticmethod
    @abstractmethod
    def extract_async(
        extractor_params: ExtractorParams,
    ) -> AsyncGenerator[ExtractedModel, None]:
        raise NotImplementedError()
