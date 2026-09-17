import csv
import json

import pytest
import requests

from g1_scraper.client import CollectionError, G1Client, SearchConfig
from g1_scraper.models import SearchResult
from g1_scraper.storage import save_csv, save_json


class FakeResponse:
    def __init__(self, *, text="", payload=None, content_type="text/html", error=None):
        self.text = text
        self.payload = payload
        self.headers = {"Content-Type": content_type}
        self.error = error

    def raise_for_status(self):
        if self.error:
            raise self.error

    def json(self):
        return self.payload


def test_client_get_shell_and_content_type_validation():
    client = G1Client(retries=0)
    client.session.get = lambda *args, **kwargs: FakeResponse(text="<html></html>")
    assert client.get_search_shell("lgpd") == "<html></html>"
    client.session.get = lambda *args, **kwargs: FakeResponse(content_type="application/json")
    with pytest.raises(CollectionError, match="não é HTML"):
        client.get_search_shell("lgpd")


def test_client_post_builds_expected_pagination():
    client = G1Client(retries=0)
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return FakeResponse(payload=[{"result": {}}], content_type="application/json")

    client.session.post = fake_post
    payload = client.post_search(SearchConfig("profile", "query", "g1"), "lgpd", 20, 10)
    assert payload == [{"result": {}}]
    assert captured["json"][0]["params"] == {"q": "lgpd", "from": 20, "size": 10}


def test_client_wraps_connection_error():
    client = G1Client(retries=0)

    def fail(*args, **kwargs):
        raise requests.ConnectionError("offline")

    client.session.post = fail
    with pytest.raises(CollectionError, match="offset=0"):
        client.post_search(SearchConfig("p", "q", "g1"), "lgpd", 0, 10)


def test_storage_writes_utf8_csv_and_json(tmp_path):
    item = SearchResult("Título", "https://g1.globo.com/a", None, None, 1, "now", "lgpd")
    csv_path, json_path = tmp_path / "out.csv", tmp_path / "out.json"
    save_csv([item], csv_path)
    save_json([item], json_path)
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        assert next(iter(csv.DictReader(stream)))["title"] == "Título"
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["summary"] is None
