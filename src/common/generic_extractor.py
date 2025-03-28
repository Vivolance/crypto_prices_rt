"""
All extractors extend this base extractor class
"""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, AsyncGenerator

from pydantic import BaseModel

from src.utils.generic_logger import logger_setup

logger: logging.Logger = logging.Logger(__name__)
logger_setup(logger)

# Create arbitrary typed variable that must implement from a BaseModel
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
