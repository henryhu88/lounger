"""
requests test sample

run test：
> pytest -vs test_api.py
"""
from pytest_req.assertions import expect

from lounger.commons.run_config import BASE_URL


def test_getting_resource(get):
    """
    Getting a resource
    """
    s = get(f"{BASE_URL}/posts/1")
    expect(s).to_be_ok()
    expect(s).to_have_path_value("userId", 1)


def test_creating_resource(post):
    """
    Creating a resource
    """
    data = {"title": "foo", "body": "bar", "userId": 1}
    s = post(f'{BASE_URL}/posts', json=data)
    expect(s).to_have_status_code(201)
    json_str = {
        "title": "foo",
        "body": "bar",
        "userId": 1,
        "id": 101
    }
    expect(s).to_have_json_matching(json_str)
