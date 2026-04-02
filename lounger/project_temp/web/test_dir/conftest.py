import pytest
from autowing.playwright.fixture import create_fixture
from dotenv import load_dotenv


@pytest.fixture
def ai(page):
    """Auto-Wing AI fixture."""
    load_dotenv()
    ai_fixture = create_fixture()
    return ai_fixture(page)
