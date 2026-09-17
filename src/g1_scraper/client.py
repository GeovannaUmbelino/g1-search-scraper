from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger(__name__)


class CollectionError(RuntimeError):
    """Falha controlada de obtenção de uma página."""


@dataclass(frozen=True, slots=True)
class SearchConfig:
    profile: str
    query_id: str
    tenant_id: str


class G1Client:
    BASE_URL = "https://g1.globo.com/busca/"
    API_URL = "https://busca.globo.com/v1/search"

    def __init__(self, timeout: tuple[float, float] = (5.0, 30.0), retries: int = 3):
        self.timeout = timeout
        self.session = requests.Session()
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST"}),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.headers.update(
    {
        "User-Agent": (
            "g1-search-scraper/1.0 "
            "(+https://github.com/GeovannaUmbelino/g1-search-scraper)"
        ),
        "Accept-Language": "pt-BR,pt;q=0.9",
    }
)

    def get_search_shell(self, term: str) -> str:
        try:
            response = self.session.get(self.BASE_URL, params={"q": term}, timeout=self.timeout)
            response.raise_for_status()
            if "text/html" not in response.headers.get("Content-Type", ""):
                raise CollectionError("Resposta da página não é HTML")
            return response.text
        except requests.RequestException as exc:
            raise CollectionError(f"Falha ao acessar a página de busca: {exc}") from exc

    def post_search(self, config: SearchConfig, term: str, offset: int, size: int) -> Any:
        body = [
            {
                "search_profile": config.profile,
                "query": config.query_id,
                "params": {"q": term, "from": offset, "size": size},
            }
        ]
        headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": config.tenant_id,
            "X-Must-Thumborize": "true",
            "X-Track-Urls": "true",
            "Origin": "https://g1.globo.com",
            "Referer": self.BASE_URL,
        }
        try:
            response = self.session.post(
                self.API_URL, json=body, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise CollectionError(f"Falha na API de busca (offset={offset}): {exc}") from exc

