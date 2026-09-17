from g1_scraper.client import CollectionError
from g1_scraper.scraper import G1Scraper, deduplicate


class FakeClient:
    def __init__(self, shell, pages):
        self.shell = shell
        self.pages = pages

    def get_search_shell(self, term):
        return self.shell

    def post_search(self, config, term, offset, size):
        value = self.pages[offset]
        if isinstance(value, Exception):
            raise value
        return value


def hit(url, title):
    return {"_source": {"url": url, "title": title, "modified": "2026-09-01T10:00:00Z"}}


def response(total, *hits):
    return [{"result": {"hits": {"total": {"value": total}, "hits": list(hits)}}}]


def test_collect_paginates_deduplicates_and_survives_page_error(fixtures_dir):
    shell = (fixtures_dir / "context.html").read_text()
    pages = {
        0: response(4, hit("https://g1.globo.com/a", "A"), hit("https://g1.globo.com/b", "B")),
        2: CollectionError("falha simulada"),
    }
    report = G1Scraper(client=FakeClient(shell, pages), page_size=2, delay=0).collect(
        "lgpd", max_pages=2
    )
    assert len(report.results) == 2
    assert report.pages_attempted == 2
    assert report.pages_succeeded == 1
    assert report.errors == ["falha simulada"]


def test_deduplicate_uses_canonical_url(fixtures_dir):
    items = G1Scraper(
        client=FakeClient((fixtures_dir / "rendered_results.html").read_text(), {})
    ).collect("lgpd").results
    unique, removed = deduplicate(items + [items[0]])
    assert len(unique) == 2
    assert removed == 1

