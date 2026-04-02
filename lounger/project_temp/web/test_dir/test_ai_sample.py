from playwright.sync_api import Page


def test_bing_search_with_ai(page: Page, base_url, ai):
    """Use Auto-Wing to perform a Bing search."""
    page.goto(base_url)

    ai.ai_action('Type "playwright" into the search input box')
    page.wait_for_timeout(3000)

    ai.ai_action("Press Enter to submit the search")
    page.wait_for_timeout(3000)

    items = ai.ai_query('string[], search result titles related to "playwright"')

    assert len(items) > 1
    assert ai.ai_assert('Check whether the first search result title contains "playwright"')
