import pytest

from api.clients.posts_api import PostsAPI
from lounger.utils.config_utils import ConfigUtils


@pytest.fixture(scope="session")
def env_config() -> dict:
    """Load the shared environment configuration."""
    config = ConfigUtils("config/config.yaml")
    return {
        "base_url": config.get_config("base_url"),
    }


@pytest.fixture()
def posts_api(env_config: dict) -> PostsAPI:
    """Posts API client fixture."""
    return PostsAPI(env_config["base_url"])
