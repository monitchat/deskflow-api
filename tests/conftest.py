import pytest

from danubio_bot.app import create_app


@pytest.fixture(scope="module")
def app():
    """Instance of App Flask"""
    return create_app()
