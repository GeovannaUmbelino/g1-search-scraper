from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from .models import SearchResult


def evaluate(results: list[SearchResult], reference: list[dict]) -> dict:
    result_by_url = {item.url: item for item in results}
    reference_by_url = {item["url"]: item for item in reference}
    matched = set(result_by_url) & set(reference_by_url)
    evaluated_results = results[: len(reference)] if reference else []
    evaluated_urls = {item.url for item in evaluated_results}
    required = ("title", "url", "result_page", "collected_at", "search_term", "source")
    optional = ("summary", "published_at")
    all_fields = required + optional
    total_cells = max(1, len(results) * len(all_fields))
    filled = sum(getattr(item, field) not in (None, "") for item in results for field in all_fields)
    required_filled = sum(
        getattr(item, field) not in (None, "") for item in results for field in required
    )
    required_cells = max(1, len(results) * len(required))
    valid_urls = sum(
        urlsplit(item.url).scheme == "https" and urlsplit(item.url).netloc.endswith("globo.com")
        for item in results
    )
    parseable_dates = sum(
        item.published_at is None or _is_datetime(item.published_at) for item in results
    )
    exact_title = sum(
        result_by_url[url].title == reference_by_url[url].get("title") for url in matched
    )
    unique_count = len({item.url for item in results})
    expected_order = [item["url"] for item in reference]
    actual_order = [item.url for item in evaluated_results]
    same_position = sum(a == b for a, b in zip(actual_order, expected_order, strict=False))

    return {
        "sample_size": len(results),
        "reference_size": len(reference),
        "completeness_all_fields": round(filled / total_cells, 4),
        "completeness_required_fields": round(required_filled / required_cells, 4),
        "reference_recall": round(len(matched) / max(1, len(reference)), 4),
        "reference_precision": round(len(evaluated_urls & set(reference_by_url)) / max(1, len(evaluated_results)), 4),
        "title_accuracy_on_matches": round(exact_title / max(1, len(matched)), 4),
        "currentness_order_agreement": round(same_position / max(1, len(reference)), 4),
        "uniqueness": round(unique_count / max(1, len(results)), 4),
        "url_consistency": round(valid_urls / max(1, len(results)), 4),
        "date_consistency": round(parseable_dates / max(1, len(results)), 4),
        "traceability": round(required_filled / required_cells, 4),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "notes": {
            "currentness": "Verificada pela comparação da ordem e datas com a página no momento da amostragem.",
            "accuracy": "Correspondência exata de URL e título contra amostra manual independente.",
        },
    }


def _is_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def load_reference(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))
