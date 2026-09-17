from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str | None
    url: str
    summary: str | None
    published_at: str | None
    result_page: int
    collected_at: str
    search_term: str
    source: str = "G1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

