from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from html import unescape
from typing import Any
from urllib.parse import (
    parse_qs,
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)

from bs4 import BeautifulSoup, Tag

from .models import SearchResult

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
}


def clean_text(value: str | None) -> str | None:
    """Remove marcação HTML e normaliza os espaços do texto."""
    if value is None:
        return None

    text = BeautifulSoup(
        unescape(value),
        "html.parser",
    ).get_text(" ", strip=True)

    normalized = re.sub(r"\s+", " ", text).strip()

    return normalized or None


def canonicalize_url(url: str) -> str:
    """Normaliza a URL e remove parâmetros conhecidos de rastreamento."""
    parts = urlsplit(url.strip())

    # Quando o rastreamento está habilitado, a API pode devolver uma URL intermediária.
    if (
        parts.netloc.lower() == "measures.globo.com"
        and parts.path == "/v1/click"
    ):
        target = parse_qs(parts.query).get("u", [])

        if target:
            return canonicalize_url(target[0])

    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parts.query)
            if key not in TRACKING_PARAMS
        )
    )

    path = parts.path.rstrip("/") or "/"

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            query,
            "",
        )
    )


def parse_context(html: str) -> dict[str, Any]:
    """Extrai o objeto window.__CONTEXT__ utilizado pela página do G1."""
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script"):
        content = script.string or script.get_text()
        marker = "window.__CONTEXT__="

        if marker not in content:
            continue

        raw = content.split(marker, 1)[1].strip().removesuffix(";")

        return json.loads(raw)

    raise ValueError("window.__CONTEXT__ não encontrado no HTML")


def _first_text(
    node: Tag,
    selectors: Iterable[str],
) -> str | None:
    """Retorna o texto do primeiro seletor encontrado."""
    for selector in selectors:
        found = node.select_one(selector)

        if found:
            return clean_text(found.decode_contents())

    return None


def parse_rendered_html(
    html: str,
    *,
    page: int,
    term: str,
    collected_at: str | None = None,
) -> list[SearchResult]:
    """Processa resultados presentes diretamente no HTML renderizado."""
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select(
        "li.widget--info, "
        "article.feed-post, "
        "div.resultado"
    )

    timestamp = (
        collected_at
        or datetime.now(timezone.utc).isoformat()
    )

    results: list[SearchResult] = []

    for card in cards:
        link = card.select_one("a[href]")

        if not link or not link.get("href"):
            continue

        url = str(link["href"])

        title = _first_text(
            card,
            [
                ".widget--info__title",
                ".feed-post-link",
                ".titulo",
            ],
        )

        summary = _first_text(
            card,
            [
                ".widget--info__description",
                ".feed-post-body-resumo",
                ".resumo",
            ],
        )

        published = _first_text(
            card,
            [
                ".widget--info__meta",
                "time",
                ".feed-post-datetime",
                ".data",
            ],
        )

        results.append(
            SearchResult(
                title=title,
                url=canonicalize_url(url),
                summary=summary,
                published_at=published,
                result_page=page,
                collected_at=timestamp,
                search_term=term,
            )
        )

    return results


def parse_api_hits(
    payload: Any,
    *,
    page: int,
    term: str,
    collected_at: str | None = None,
) -> tuple[list[SearchResult], int]:
    """Converte a resposta da busca em registros tipados."""
    timestamp = (
        collected_at
        or datetime.now(timezone.utc).isoformat()
    )

    if isinstance(payload, list) and payload:
        response = payload[0].get("result", {})
    else:
        response = payload or {}

    if isinstance(response, dict):
        hits_container = response.get("hits", {})
    else:
        hits_container = {}

    if isinstance(hits_container, dict):
        hits = hits_container.get("hits", [])
        total_raw = hits_container.get("total", 0)
    else:
        hits = []
        total_raw = 0

    if isinstance(total_raw, dict):
        total = total_raw.get("value", 0)
    else:
        total = int(total_raw or 0)

    results: list[SearchResult] = []

    for hit in hits:
        if isinstance(hit, dict):
            source = hit.get("_source", {})
        else:
            source = {}

        url = source.get("url")

        # A URL é o campo mínimo necessário para identificar,rastrear e deduplicar um resultado.
        if not url:
            continue

        summary = (
            source.get("body")
            or source.get("description")
            or source.get("subtitle")
            or source.get("subtitulo")
        )

        results.append(
            SearchResult(
                title=clean_text(source.get("title")),
                url=canonicalize_url(str(url)),
                summary=_truncate(
                    clean_text(summary),
                    300,
                ),
                published_at=(
                    source.get("modified")
                    or source.get("publicationDate")
                ),
                result_page=page,
                collected_at=timestamp,
                search_term=term,
            )
        )

    return results, total


def _truncate(
    value: str | None,
    size: int,
) -> str | None:
    """Trunca um texto sem dividir a última palavra, quando possível."""
    if value is None or len(value) <= size:
        return value

    truncated = value[:size]

 
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]

    truncated = truncated.rstrip(".,;:!? ")

    return f"{truncated}..."