import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Page


def screenshot_base64(page: "Page"):
    """
    Obtain a base64 encoded screenshot
    :param page:
    :return:
    """
    # Lazy import to avoid import errors when playwright is not properly installed
    img = page.screenshot(type='png', path=None)
    img_base64 = base64.b64encode(img).decode('utf-8')
    return img_base64
