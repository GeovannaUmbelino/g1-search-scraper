import json

from g1_scraper.cli import build_parser, main
from g1_scraper.client import CollectionError
from g1_scraper.models import SearchResult
from g1_scraper.scraper import ScrapeReport


def make_report() -> ScrapeReport:
    """Cria um relatório simulado para os testes da CLI."""
    result = SearchResult(
        title="Notícia sobre LGPD",
        url="https://g1.globo.com/noticia",
        summary="Resumo da notícia",
        published_at="2026-09-15T10:00:00+00:00",
        result_page=1,
        collected_at="2026-09-15T11:00:00+00:00",
        search_term="lgpd",
    )

    return ScrapeReport(
        results=[result],
        pages_attempted=1,
        pages_succeeded=1,
        duplicates_removed=0,
        errors=[],
    )


def test_build_parser_uses_default_values():
    """Verifica os valores padrão dos argumentos da CLI."""
    args = build_parser().parse_args([])

    assert args.term == "lgpd"
    assert args.max_pages == 5
    assert args.page_size == 10
    assert args.delay == 1.0
    assert args.output_dir.name == "processed"
    assert args.reference.name == "manual_sample.json"
    assert args.log_level == "INFO"


def test_main_collects_and_saves_results(monkeypatch, tmp_path):
    """Verifica a execução e a geração dos arquivos."""
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "g1_scraper.cli.G1Scraper.collect",
        lambda self, term, max_pages: make_report(),
    )

    output_dir = tmp_path / "data"
    reference_path = tmp_path / "reference-inexistente.json"

    exit_code = main(
        [
            "--term",
            "lgpd",
            "--max-pages",
            "1",
            "--page-size",
            "10",
            "--delay",
            "0",
            "--output-dir",
            str(output_dir),
            "--reference",
            str(reference_path),
            "--log-level",
            "INFO",
        ]
    )

    assert exit_code == 0

    csv_path = output_dir / "g1_lgpd.csv"
    json_path = output_dir / "g1_lgpd.json"
    summary_path = tmp_path / "reports" / "run_summary.json"

    assert csv_path.exists()
    assert json_path.exists()
    assert summary_path.exists()

    results = json.loads(json_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert len(results) == 1
    assert results[0]["title"] == "Notícia sobre LGPD"
    assert results[0]["search_term"] == "lgpd"

    assert summary["records"] == 1
    assert summary["pages_attempted"] == 1
    assert summary["pages_succeeded"] == 1
    assert summary["duplicates_removed"] == 0
    assert summary["errors"] == []


def test_main_generates_quality_metrics_when_reference_exists(
    monkeypatch,
    tmp_path,
):
    """Verifica a geração das métricas quando existe uma referência."""
    monkeypatch.chdir(tmp_path)

    report = make_report()

    monkeypatch.setattr(
        "g1_scraper.cli.G1Scraper.collect",
        lambda self, term, max_pages: report,
    )

    reference_path = tmp_path / "manual_sample.json"
    reference = [
        {
            "rank": 1,
            "title": report.results[0].title,
            "url": report.results[0].url,
            "published_at": report.results[0].published_at,
            "result_page": 1,
            "observed_at": "2026-09-15T11:00:00+00:00",
        }
    ]

    reference_path.write_text(
        json.dumps(reference, ensure_ascii=False),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--term",
            "lgpd",
            "--max-pages",
            "1",
            "--delay",
            "0",
            "--output-dir",
            str(tmp_path / "data"),
            "--reference",
            str(reference_path),
        ]
    )

    metrics_path = tmp_path / "reports" / "quality_metrics.json"

    assert exit_code == 0
    assert metrics_path.exists()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert metrics["sample_size"] == 1
    assert metrics["reference_size"] == 1
    assert metrics["reference_recall"] == 1.0
    assert metrics["reference_precision"] == 1.0
    assert metrics["title_accuracy_on_matches"] == 1.0
    assert metrics["currentness_order_agreement"] == 1.0
    assert metrics["uniqueness"] == 1.0
    assert metrics["traceability"] == 1.0


def test_main_returns_one_when_all_pages_fail(
    monkeypatch,
    tmp_path,
):
    """Verifica o código de saída quando nenhuma página é coletada."""
    monkeypatch.chdir(tmp_path)

    report = ScrapeReport(
        results=[],
        pages_attempted=1,
        pages_succeeded=0,
        duplicates_removed=0,
        errors=["falha simulada"],
    )

    monkeypatch.setattr(
        "g1_scraper.cli.G1Scraper.collect",
        lambda self, term, max_pages: report,
    )

    exit_code = main(
        [
            "--output-dir",
            str(tmp_path / "data"),
            "--reference",
            str(tmp_path / "reference-inexistente.json"),
        ]
    )

    summary_path = tmp_path / "reports" / "run_summary.json"

    assert exit_code == 1
    assert summary_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["records"] == 0
    assert summary["pages_attempted"] == 1
    assert summary["pages_succeeded"] == 0
    assert summary["errors"] == ["falha simulada"]


def test_main_returns_two_when_initial_collection_fails(
    monkeypatch,
    tmp_path,
):
    """Verifica o código de saída para uma falha inicial controlada."""
    monkeypatch.chdir(tmp_path)

    def raise_collection_error(self, term, max_pages):
        raise CollectionError("falha inicial simulada")

    monkeypatch.setattr(
        "g1_scraper.cli.G1Scraper.collect",
        raise_collection_error,
    )

    output_dir = tmp_path / "data"

    exit_code = main(
        [
            "--term",
            "lgpd",
            "--output-dir",
            str(output_dir),
        ]
    )

    assert exit_code == 2
    assert not output_dir.exists()
    assert not (tmp_path / "reports" / "run_summary.json").exists()