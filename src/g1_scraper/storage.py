from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import SearchResult

FIELDS = [
    "title", "url", "summary", "published_at", "result_page", "collected_at",
    "search_term", "source",
]


def save_csv(results: list[SearchResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(item.to_dict() for item in results)


def save_json(results: list[SearchResult], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump([item.to_dict() for item in results], stream, ensure_ascii=False, indent=2)

