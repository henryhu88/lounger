from lounger.request import HttpRequest, api


class PostsAPI(HttpRequest):
    """Posts API client."""

    def __init__(self, base_url: str):
        super().__init__(base_url=base_url)

    @api(describe="Get a post", status_code=200)
    def get_post(self, post_id: int):
        """Fetch a post by ID."""
        return self.get(f"/posts/{post_id}")

    @api(describe="Create a post", status_code=201)
    def create_post(self, payload: dict):
        """Create a post."""
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
        }
        return self.post("/posts", json=payload, headers=headers)
