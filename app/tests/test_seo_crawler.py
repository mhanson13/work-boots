from __future__ import annotations

from app.services.seo_crawler import FetchResponse, SEOCrawler


class _FakeCrawler(SEOCrawler):
    def __init__(self, pages: dict[str, FetchResponse]) -> None:
        super().__init__(timeout_seconds=1)
        self.pages = pages
        self.requested: list[str] = []

    def _fetch(self, url: str) -> FetchResponse:  # type: ignore[override]
        self.requested.append(url)
        return self.pages[url]


def test_crawler_is_bounded_and_same_domain_only() -> None:
    pages = {
        "https://example.com/": FetchResponse(
            final_url="https://example.com/",
            status_code=200,
            body=(
                '<a href="/a">A</a>'
                '<a href="/b?x=1&y=2">B1</a>'
                '<a href="https://external.example/page">EXT</a>'
                '<a href="ftp://example.com/file.txt">FTP</a>'
            ),
        ),
        "https://example.com/a": FetchResponse(
            final_url="https://example.com/a",
            status_code=200,
            body='<a href="/b?y=2&x=1">B2</a><a href="/c">C</a>',
        ),
        "https://example.com/b?x=1&y=2": FetchResponse(
            final_url="https://example.com/b?x=1&y=2",
            status_code=200,
            body="<p>page b</p>",
        ),
        "https://example.com/c": FetchResponse(
            final_url="https://example.com/c",
            status_code=200,
            body="<p>page c</p>",
        ),
    }
    crawler = _FakeCrawler(pages)

    limited = crawler.crawl(
        base_url="https://example.com/",
        max_pages=2,
        max_depth=3,
        same_domain_only=True,
    )
    assert len(limited) == 2
    assert all(item.final_url.startswith("https://example.com/") for item in limited)

    full = crawler.crawl(
        base_url="https://example.com/",
        max_pages=10,
        max_depth=3,
        same_domain_only=True,
    )
    crawled_urls = [item.final_url for item in full]
    assert "https://example.com/b?x=1&y=2" in crawled_urls
    assert crawled_urls.count("https://example.com/b?x=1&y=2") == 1
