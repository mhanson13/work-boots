from __future__ import annotations

import logging
from datetime import timedelta
from uuid import uuid4

import pytest

from app.cli import seo_competitor_profile_generation_retention_cleanup as retention_cli
from app.core.time import utc_now
from app.models.business import Business
from app.models.seo_competitor_profile_draft import SEOCompetitorProfileDraft
from app.models.seo_competitor_profile_generation_run import SEOCompetitorProfileGenerationRun
from app.models.seo_site import SEOSite


class _SessionContext:
    def __init__(self, session) -> None:
        self._session = session

    def __enter__(self):
        return self._session

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _patch_cli_session(monkeypatch: pytest.MonkeyPatch, db_session) -> None:
    monkeypatch.setattr(retention_cli, "SessionLocal", lambda: _SessionContext(db_session))


def _create_business(db_session, *, name: str) -> Business:
    business = Business(
        id=str(uuid4()),
        name=name,
        notification_phone="+13035557777",
        notification_email=f"{name.lower().replace(' ', '')}@example.com",
        sms_enabled=True,
        email_enabled=True,
        customer_auto_ack_enabled=True,
        contractor_alerts_enabled=True,
        timezone="America/Denver",
    )
    db_session.add(business)
    db_session.commit()
    return business


def _create_site(db_session, *, business_id: str, domain: str) -> SEOSite:
    site = SEOSite(
        id=str(uuid4()),
        business_id=business_id,
        display_name=f"Site {domain}",
        base_url=f"https://{domain}/",
        normalized_domain=domain,
        is_active=True,
        is_primary=False,
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


def _create_run(
    db_session,
    *,
    business_id: str,
    site_id: str,
    age_days: int,
    raw_output: str,
) -> SEOCompetitorProfileGenerationRun:
    timestamp = utc_now() - timedelta(days=age_days)
    run = SEOCompetitorProfileGenerationRun(
        id=str(uuid4()),
        business_id=business_id,
        site_id=site_id,
        parent_run_id=None,
        status="completed",
        requested_candidate_count=2,
        generated_draft_count=1,
        provider_name="openai",
        model_name="gpt-4o-mini",
        prompt_version="seo-competitor-profile-v1",
        raw_output=raw_output,
        error_summary=None,
        completed_at=timestamp,
        created_by_principal_id=None,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


def _create_rejected_draft(
    db_session,
    *,
    business_id: str,
    site_id: str,
    run_id: str,
    age_days: int,
) -> SEOCompetitorProfileDraft:
    timestamp = utc_now() - timedelta(days=age_days)
    draft = SEOCompetitorProfileDraft(
        id=str(uuid4()),
        business_id=business_id,
        site_id=site_id,
        generation_run_id=run_id,
        suggested_name="Competitor",
        suggested_domain=f"{uuid4().hex[:10]}.example",
        competitor_type="direct",
        summary="summary",
        why_competitor="why",
        evidence="evidence",
        confidence_score=0.75,
        source="ai_generated",
        review_status="rejected",
        reviewed_by_principal_id="reviewer",
        reviewed_at=timestamp,
        accepted_competitor_set_id=None,
        accepted_competitor_domain_id=None,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db_session.add(draft)
    db_session.commit()
    db_session.refresh(draft)
    return draft


def test_retention_cleanup_cli_global_scope_runs_cleanup_for_all_businesses(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_cli_session(monkeypatch, db_session)

    other_business = _create_business(db_session, name="Other Tenant")
    site_a = _create_site(db_session, business_id=seeded_business.id, domain="tenant-a-cleanup.example")
    site_b = _create_site(db_session, business_id=other_business.id, domain="tenant-b-cleanup.example")

    run_a = _create_run(
        db_session,
        business_id=seeded_business.id,
        site_id=site_a.id,
        age_days=120,
        raw_output='{"debug":"tenant-a"}',
    )
    run_b = _create_run(
        db_session,
        business_id=other_business.id,
        site_id=site_b.id,
        age_days=120,
        raw_output='{"debug":"tenant-b"}',
    )
    _create_rejected_draft(
        db_session,
        business_id=seeded_business.id,
        site_id=site_a.id,
        run_id=run_a.id,
        age_days=120,
    )
    _create_rejected_draft(
        db_session,
        business_id=other_business.id,
        site_id=site_b.id,
        run_id=run_b.id,
        age_days=120,
    )

    summary = retention_cli.run_seo_competitor_profile_generation_retention_cleanup(
        business_id=None,
        site_id=None,
    )

    assert summary["scope"] == "global"
    assert summary["businesses_scanned"] == 2
    assert summary["businesses_succeeded"] == 2
    assert summary["businesses_failed"] == 0

    totals = summary["totals"]
    assert isinstance(totals, dict)
    assert totals["raw_output_pruned_runs"] == 2
    assert totals["rejected_drafts_pruned"] == 2

    assert db_session.get(SEOCompetitorProfileGenerationRun, run_a.id).raw_output is None
    assert db_session.get(SEOCompetitorProfileGenerationRun, run_b.id).raw_output is None


def test_retention_cleanup_cli_is_idempotent_on_repeated_runs(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_cli_session(monkeypatch, db_session)

    site = _create_site(db_session, business_id=seeded_business.id, domain="idempotent-cleanup.example")
    run = _create_run(
        db_session,
        business_id=seeded_business.id,
        site_id=site.id,
        age_days=120,
        raw_output='{"debug":"payload"}',
    )
    _create_rejected_draft(
        db_session,
        business_id=seeded_business.id,
        site_id=site.id,
        run_id=run.id,
        age_days=120,
    )

    first = retention_cli.run_seo_competitor_profile_generation_retention_cleanup(
        business_id=seeded_business.id,
        site_id=None,
    )
    second = retention_cli.run_seo_competitor_profile_generation_retention_cleanup(
        business_id=seeded_business.id,
        site_id=None,
    )

    first_totals = first["totals"]
    second_totals = second["totals"]
    assert isinstance(first_totals, dict)
    assert isinstance(second_totals, dict)
    assert first_totals["raw_output_pruned_runs"] == 1
    assert first_totals["rejected_drafts_pruned"] == 1
    assert second_totals["raw_output_pruned_runs"] == 0
    assert second_totals["rejected_drafts_pruned"] == 0


def test_retention_cleanup_cli_logs_start_and_completion(
    db_session,
    seeded_business,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    _patch_cli_session(monkeypatch, db_session)
    caplog.set_level(logging.INFO)

    summary = retention_cli.run_seo_competitor_profile_generation_retention_cleanup(
        business_id=seeded_business.id,
        site_id=None,
    )

    assert summary["businesses_scanned"] == 1
    assert any("cleanup sweep started" in record.message for record in caplog.records)
    assert any("cleanup sweep completed" in record.message for record in caplog.records)


def test_retention_cleanup_cli_rejects_site_scope_without_business_id() -> None:
    with pytest.raises(ValueError, match="--site-id requires --business-id"):
        retention_cli.run_seo_competitor_profile_generation_retention_cleanup(
            business_id=None,
            site_id="site-1",
        )
