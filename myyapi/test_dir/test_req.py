"""
requests demo

run test：
> pytest -vs --base-url https://httpbin.org test_request.py
"""
from pytest_req.assertions import expect
from lounger.commons.run_config import BASE_URL

def test_post_method(post):
    """
    test post request
    """
    s = post(f'{BASE_URL}/login', data={"username": "admin", "password": "a123456"})
    expect(s).to_be_ok()


def test_get_method(get):
    """
    test get request
    """
    s = get(f"{BASE_URL}/add_one")
    expect(s).to_be_ok()
