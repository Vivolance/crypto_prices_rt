import pytest


ENDPOINT_URL: str = "localhost:9001"
ACCESS_KEY_ID: str = "my_dummy_access_key"
SECRET_ACCESS_KEY_ID: str = "my_dummy_password"


class TestS3UploaderThread:
    @pytest.fixture
    def bucket_name(self) -> str:
        pass
