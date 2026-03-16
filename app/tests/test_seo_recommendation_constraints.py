from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.seo_audit_run import SEOAuditRun
from app.models.seo_recommendation import SEORecommendation
from app.models.seo_recommendation_run import SEORecommendationRun
from app.models.seo_site import SEOSite
from app.repositories.seo_recommendation_repository import SEORecommendationRepository


def _seed_site(db_session, *, business_id: str, domain: str) -> SEOSite:
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
    db_session.flush()
    return site


def _seed_completed_audit_run(db_session, *, business_id: str, site_id: str) -> SEOAuditRun:
    run = SEOAuditRun(
        id=str(uuid4()),
        business_id=business_id,
        site_id=site_id,
        status="completed",
        max_pages=10,
        max_depth=2,
    )
    db_session.add(run)
    db_session.flush()
    return run


def test_recommendation_run_requires_input_lineage(db_session, seeded_business) -> None:
    site = _seed_site(db_session, business_id=seeded_business.id, domain="client.example")
    db_session.add(
        SEORecommendationRun(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            audit_run_id=None,
            comparison_run_id=None,
            status="queued",
            total_recommendations=0,
            critical_recommendations=0,
            warning_recommendations=0,
            info_recommendations=0,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_recommendation_repository_rejects_lineage_scope_mismatch(db_session, seeded_business) -> None:
    repo = SEORecommendationRepository(db_session)
    site_a = _seed_site(db_session, business_id=seeded_business.id, domain="a.example")
    site_b = _seed_site(db_session, business_id=seeded_business.id, domain="b.example")
    audit_run = _seed_completed_audit_run(db_session, business_id=seeded_business.id, site_id=site_a.id)

    with pytest.raises(ValueError, match="Audit run scope mismatch"):
        repo.create_run(
            SEORecommendationRun(
                id=str(uuid4()),
                business_id=seeded_business.id,
                site_id=site_b.id,
                audit_run_id=audit_run.id,
                comparison_run_id=None,
                status="queued",
                total_recommendations=0,
                critical_recommendations=0,
                warning_recommendations=0,
                info_recommendations=0,
            )
        )


def test_recommendation_unique_rule_key_per_run(db_session, seeded_business) -> None:
    repo = SEORecommendationRepository(db_session)
    site = _seed_site(db_session, business_id=seeded_business.id, domain="client.example")
    audit_run = _seed_completed_audit_run(db_session, business_id=seeded_business.id, site_id=site.id)
    recommendation_run = repo.create_run(
        SEORecommendationRun(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            audit_run_id=audit_run.id,
            comparison_run_id=None,
            status="completed",
            total_recommendations=0,
            critical_recommendations=0,
            warning_recommendations=0,
            info_recommendations=0,
        )
    )
    db_session.flush()

    repo.add_recommendation(
        SEORecommendation(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            recommendation_run_id=recommendation_run.id,
            audit_run_id=audit_run.id,
            comparison_run_id=None,
            rule_key="fix_missing_title_tags",
            category="SEO",
            severity="CRITICAL",
            title="Fix missing title tags",
            rationale="deterministic rationale",
            priority_score=90,
            effort_bucket="LOW",
            evidence_json={"counts": {"missing_title": 2}},
        )
    )
    db_session.flush()

    db_session.add(
        SEORecommendation(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site.id,
            recommendation_run_id=recommendation_run.id,
            audit_run_id=audit_run.id,
            comparison_run_id=None,
            rule_key="fix_missing_title_tags",
            category="SEO",
            severity="CRITICAL",
            title="Fix missing title tags",
            rationale="duplicate deterministic rationale",
            priority_score=88,
            effort_bucket="LOW",
            evidence_json={"counts": {"missing_title": 1}},
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_recommendation_repository_rejects_run_scope_mismatch_on_add(db_session, seeded_business) -> None:
    repo = SEORecommendationRepository(db_session)
    site_a = _seed_site(db_session, business_id=seeded_business.id, domain="a.example")
    site_b = _seed_site(db_session, business_id=seeded_business.id, domain="b.example")
    audit_run_a = _seed_completed_audit_run(db_session, business_id=seeded_business.id, site_id=site_a.id)
    recommendation_run = repo.create_run(
        SEORecommendationRun(
            id=str(uuid4()),
            business_id=seeded_business.id,
            site_id=site_a.id,
            audit_run_id=audit_run_a.id,
            comparison_run_id=None,
            status="queued",
            total_recommendations=0,
            critical_recommendations=0,
            warning_recommendations=0,
            info_recommendations=0,
        )
    )
    db_session.flush()

    with pytest.raises(ValueError, match="Recommendation scope mismatch"):
        repo.add_recommendation(
            SEORecommendation(
                id=str(uuid4()),
                business_id=seeded_business.id,
                site_id=site_b.id,
                recommendation_run_id=recommendation_run.id,
                audit_run_id=audit_run_a.id,
                comparison_run_id=None,
                rule_key="fix_missing_title_tags",
                category="SEO",
                severity="CRITICAL",
                title="Fix missing title tags",
                rationale="deterministic rationale",
                priority_score=90,
                effort_bucket="LOW",
                evidence_json={"counts": {"missing_title": 2}},
            )
        )
