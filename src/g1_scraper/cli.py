from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .client import CollectionError
from .quality import evaluate, load_reference
from .scraper import G1Scraper
from .storage import save_csv, save_json

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Coleta resultados da busca do G1")
    parser.add_argument("--term", default="lgpd", help="termo de busca")
    parser.add_argument("--max-pages", type=int, default=5)
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--delay", type=float, default=1.0, help="intervalo entre páginas")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--reference", type=Path, default=Path("data/reference/manual_sample.json"))
    parser.add_argument("--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        report = G1Scraper(page_size=args.page_size, delay=args.delay).collect(
            args.term, max_pages=args.max_pages
        )
    except CollectionError as exc:
        LOGGER.error("Coleta abortada de forma controlada: %s", exc)
        return 2

    csv_path = args.output_dir / f"g1_{args.term}.csv"
    json_path = args.output_dir / f"g1_{args.term}.json"
    save_csv(report.results, csv_path)
    save_json(report.results, json_path)

    summary = {
        "records": len(report.results),
        "pages_attempted": report.pages_attempted,
        "pages_succeeded": report.pages_succeeded,
        "duplicates_removed": report.duplicates_removed,
        "errors": report.errors,
    }
    Path("reports").mkdir(exist_ok=True)
    Path("reports/run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.reference.exists():
        metrics = evaluate(report.results, load_reference(args.reference))
        Path("reports/quality_metrics.json").write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 0 if report.pages_succeeded else 1


if __name__ == "__main__":
    sys.exit(main())
