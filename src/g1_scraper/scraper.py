from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .client import CollectionError, G1Client, SearchConfig
from .models import SearchResult
from .parsers import parse_api_hits, parse_context, parse_rendered_html

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ScrapeReport:
    results: list[SearchResult]
    pages_attempted: int
    pages_succeeded: int
    duplicates_removed: int
    errors: list[str]


def config_from_context(context: dict) -> SearchConfig:
    resource = context["api_content"]["resource"]
    config = resource["config"]
    query_ids = config["queryId"]
    return SearchConfig(
        profile=config["searchProfile"],
        query_id=query_ids.get("recent") or query_ids["relevant"],
        tenant_id=resource["tenantId"],
    )


def deduplicate(results: list[SearchResult]) -> tuple[list[SearchResult], int]:
    unique: dict[str, SearchResult] = {}
    for item in results:
        unique.setdefault(item.url, item)
    return list(unique.values()), len(results) - len(unique)


class G1Scraper:
    def __init__(self, client: G1Client | None = None, page_size: int = 10, delay: float = 1.0):
        self.client = client or G1Client()
        self.page_size = page_size
        self.delay = delay

    def collect(self, term: str, max_pages: int = 5) -> ScrapeReport:
        errors: list[str] = []
        attempted = succeeded = 0
        LOGGER.info("Obtendo configuração atual da busca para termo=%r", term)
        shell = self.client.get_search_shell(term)

        rendered = parse_rendered_html(shell, page=1, term=term)
        if rendered:
            LOGGER.info("Resultados encontrados diretamente no HTML: %d", len(rendered))
            unique, removed = deduplicate(rendered)
            return ScrapeReport(unique, 1, 1, removed, errors)

        try:
            config = config_from_context(parse_context(shell))
        except (KeyError, TypeError, ValueError) as exc:
            raise CollectionError(f"Não foi possível descobrir a configuração da busca: {exc}") from exc

        all_results: list[SearchResult] = []
        total: int | None = None
        page = 1
        while page <= max_pages and (total is None or len(all_results) < total):
            attempted += 1
            offset = (page - 1) * self.page_size
            LOGGER.info("Coletando página=%d offset=%d", page, offset)
            try:
                payload = self.client.post_search(config, term, offset, self.page_size)
                current, total_found = parse_api_hits(payload, page=page, term=term)
                total = total_found
                succeeded += 1
                LOGGER.info("Página=%d: %d registros; total informado=%d", page, len(current), total)
                if not current:
                    LOGGER.warning("Página=%d vazia; paginação encerrada para evitar loop", page)
                    break
                all_results.extend(current)
            except CollectionError as exc:
                message = str(exc)
                errors.append(message)
                LOGGER.error(message)
            page += 1
            if page <= max_pages:
                time.sleep(self.delay)

        unique, removed = deduplicate(all_results)
        LOGGER.info(
            "Coleta concluída: %d únicos, %d duplicados removidos, %d/%d páginas com sucesso",
            len(unique), removed, succeeded, attempted,
        )
        return ScrapeReport(unique, attempted, succeeded, removed, errors)
