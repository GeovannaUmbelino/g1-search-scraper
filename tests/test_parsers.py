import pytest

from g1_scraper.parsers import (
    canonicalize_url,
    clean_text,
    parse_api_hits,
    parse_context,
    parse_rendered_html,
)


def test_clean_text_removes_markup_and_normalizes_spaces():
    assert (
        clean_text(" Olá <strong>LGPD</strong>  &amp; dados ")
        == "Olá LGPD & dados"
    )
    assert clean_text(None) is None
    assert clean_text("   ") is None


def test_canonicalize_url_removes_fragment_and_tracking():
    url = "HTTPS://G1.GLOBO.COM/a/?utm_source=x&b=2#top"

    assert canonicalize_url(url) == "https://g1.globo.com/a?b=2"


def test_canonicalize_url_unwraps_g1_tracking_redirect():
    redirect = (
        "https://measures.globo.com/v1/click?"
        "x=1&u=https%3A%2F%2Fg1.globo.com%2Freal%2F"
    )

    assert canonicalize_url(redirect) == "https://g1.globo.com/real"


def test_parse_context(fixtures_dir):
    html = (
        fixtures_dir / "context.html"
    ).read_text(encoding="utf-8")

    context = parse_context(html)

    assert context["api_content"]["resource"]["tenantId"] == "g1"


def test_parse_context_raises_error_when_context_is_missing():
    with pytest.raises(
        ValueError,
        match="window.__CONTEXT__ não encontrado",
    ):
        parse_context("<html><body>Sem contexto</body></html>")


def test_parse_rendered_html_handles_missing_optional_fields(
    fixtures_dir,
):
    html = (
        fixtures_dir / "rendered_results.html"
    ).read_text(encoding="utf-8")

    results = parse_rendered_html(
        html,
        page=2,
        term="lgpd",
        collected_at="2026-09-15T00:00:00+00:00",
    )

    assert len(results) == 2

    assert results[0].title == "Título & teste"
    assert results[0].summary == "Resumo com LGPD ."
    assert results[0].url == "https://g1.globo.com/a/noticia"
    assert results[0].result_page == 2
    assert results[0].search_term == "lgpd"

    assert results[1].title == "Sem campos opcionais"
    assert results[1].summary is None
    assert results[1].published_at is None
    assert results[1].result_page == 2


def test_parse_api_hits_tolerates_missing_fields_and_skips_no_url():
    payload = [
        {
            "result": {
                "hits": {
                    "total": {"value": 3},
                    "hits": [
                        {
                            "_source": {
                                "title": "Primeiro",
                                "url": "https://g1.globo.com/1/",
                                "body": "A <b>LGPD</b>",
                                "modified": (
                                    "2026-09-01T10:00:00Z"
                                ),
                            }
                        },
                        {
                            "_source": {
                                "title": "Segundo",
                                "url": "https://g1.globo.com/2",
                            }
                        },
                        {
                            "_source": {
                                "title": "Inválido sem URL",
                            }
                        },
                    ],
                }
            }
        }
    ]

    results, total = parse_api_hits(
        payload,
        page=1,
        term="lgpd",
        collected_at="2026-09-15T10:00:00+00:00",
    )

    assert total == 3
    assert len(results) == 2
    assert results[0].summary == "A LGPD"
    assert results[1].published_at is None


def test_parse_api_hits_accepts_numeric_total():
    payload = {
        "hits": {
            "total": 1,
            "hits": [
                {
                    "_source": {
                        "title": "Resultado",
                        "url": "https://g1.globo.com/resultado",
                    }
                }
            ],
        }
    }

    results, total = parse_api_hits(
        payload,
        page=1,
        term="lgpd",
        collected_at="2026-09-15T10:00:00+00:00",
    )

    assert total == 1
    assert len(results) == 1


def test_parse_api_hits_handles_empty_payload():
    results, total = parse_api_hits(
        [],
        page=1,
        term="lgpd",
        collected_at="2026-09-15T10:00:00+00:00",
    )

    assert results == []
    assert total == 0


def test_parse_api_hits_truncates_summary_without_splitting_word():
    long_summary = (
        "A Lei Geral de Proteção de Dados estabelece regras "
        "para o tratamento responsável de informações pessoais. "
        * 10
    ).strip()

    payload = [
        {
            "result": {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_source": {
                                "title": "Título",
                                "url": (
                                    "https://g1.globo.com/noticia"
                                ),
                                "body": long_summary,
                            }
                        }
                    ],
                }
            }
        }
    ]

    results, total = parse_api_hits(
        payload,
        page=1,
        term="lgpd",
        collected_at="2026-09-15T10:00:00+00:00",
    )

    summary = results[0].summary

    assert total == 1
    assert len(results) == 1
    assert summary is not None
    assert summary.endswith("...")
    assert len(summary) <= 303

    text_without_ellipsis = summary.removesuffix("...")

    assert not text_without_ellipsis.endswith(" ")
    assert text_without_ellipsis[-1].isalnum()


def test_short_summary_is_not_modified():
    payload = [
        {
            "result": {
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_source": {
                                "title": "Título",
                                "url": (
                                    "https://g1.globo.com/noticia"
                                ),
                                "body": "Resumo curto.",
                            }
                        }
                    ],
                }
            }
        }
    ]

    results, total = parse_api_hits(
        payload,
        page=1,
        term="lgpd",
        collected_at="2026-09-15T10:00:00+00:00",
    )

    assert total == 1
    assert results[0].summary == "Resumo curto."