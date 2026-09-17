from g1_scraper.models import SearchResult
from g1_scraper.quality import evaluate


def test_quality_metrics_are_objective_and_bounded():
    result = SearchResult(
        "Título", "https://g1.globo.com/a", None, "2026-09-01T10:00:00Z", 1,
        "2026-09-15T10:00:00+00:00", "lgpd",
    )
    metrics = evaluate([result], [{"url": result.url, "title": result.title}])
    assert metrics["reference_recall"] == 1.0
    assert metrics["title_accuracy_on_matches"] == 1.0
    assert metrics["currentness_order_agreement"] == 1.0
    assert metrics["uniqueness"] == 1.0
    assert 0 <= metrics["completeness_all_fields"] <= 1
