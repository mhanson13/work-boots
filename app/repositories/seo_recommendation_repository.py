from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.seo_audit_run import SEOAuditRun
from app.models.seo_competitor_comparison_run import SEOCompetitorComparisonRun
from app.models.seo_recommendation import SEORecommendation
from app.models.seo_recommendation_run import SEORecommendationRun
from app.models.seo_site import SEOSite


class SEORecommendationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_run(self, run: SEORecommendationRun) -> SEORecommendationRun:
        site = self.session.scalar(
            select(SEOSite.id)
            .where(SEOSite.business_id == run.business_id)
            .where(SEOSite.id == run.site_id)
        )
        if site is None:
            raise ValueError("SEO site not found for business")

        if run.audit_run_id is not None:
            audit_run = self.session.scalar(select(SEOAuditRun).where(SEOAuditRun.id == run.audit_run_id))
            if audit_run is None:
                raise ValueError("Audit run not found")
            if audit_run.business_id != run.business_id or audit_run.site_id != run.site_id:
                raise ValueError("Audit run scope mismatch")

        if run.comparison_run_id is not None:
            comparison_run = self.session.scalar(
                select(SEOCompetitorComparisonRun).where(SEOCompetitorComparisonRun.id == run.comparison_run_id)
            )
            if comparison_run is None:
                raise ValueError("Comparison run not found")
            if comparison_run.business_id != run.business_id or comparison_run.site_id != run.site_id:
                raise ValueError("Comparison run scope mismatch")

        self.session.add(run)
        self.session.flush()
        return run

    def save_run(self, run: SEORecommendationRun) -> SEORecommendationRun:
        self.session.add(run)
        self.session.flush()
        return run

    def get_run_for_business(self, business_id: str, recommendation_run_id: str) -> SEORecommendationRun | None:
        stmt: Select[tuple[SEORecommendationRun]] = (
            select(SEORecommendationRun)
            .where(SEORecommendationRun.business_id == business_id)
            .where(SEORecommendationRun.id == recommendation_run_id)
        )
        return self.session.scalar(stmt)

    def list_runs_for_business_site(self, business_id: str, site_id: str) -> list[SEORecommendationRun]:
        stmt: Select[tuple[SEORecommendationRun]] = (
            select(SEORecommendationRun)
            .where(SEORecommendationRun.business_id == business_id)
            .where(SEORecommendationRun.site_id == site_id)
            .order_by(SEORecommendationRun.created_at.desc(), SEORecommendationRun.id.desc())
        )
        return list(self.session.scalars(stmt))

    def add_recommendation(self, recommendation: SEORecommendation) -> SEORecommendation:
        run = self.session.scalar(
            select(SEORecommendationRun).where(SEORecommendationRun.id == recommendation.recommendation_run_id)
        )
        if run is None:
            raise ValueError("Recommendation run not found")
        if run.business_id != recommendation.business_id or run.site_id != recommendation.site_id:
            raise ValueError("Recommendation scope mismatch")

        if run.audit_run_id is not None and recommendation.audit_run_id != run.audit_run_id:
            raise ValueError("Recommendation audit run mismatch")
        if run.comparison_run_id is not None and recommendation.comparison_run_id != run.comparison_run_id:
            raise ValueError("Recommendation comparison run mismatch")

        self.session.add(recommendation)
        self.session.flush()
        return recommendation

    def list_recommendations_for_business_run(
        self,
        business_id: str,
        recommendation_run_id: str,
    ) -> list[SEORecommendation]:
        stmt: Select[tuple[SEORecommendation]] = (
            select(SEORecommendation)
            .where(SEORecommendation.business_id == business_id)
            .where(SEORecommendation.recommendation_run_id == recommendation_run_id)
            .order_by(
                SEORecommendation.priority_score.desc(),
                SEORecommendation.created_at.asc(),
                SEORecommendation.id.asc(),
            )
        )
        return list(self.session.scalars(stmt))

    def get_recommendation_for_business(self, business_id: str, recommendation_id: str) -> SEORecommendation | None:
        stmt: Select[tuple[SEORecommendation]] = (
            select(SEORecommendation)
            .where(SEORecommendation.business_id == business_id)
            .where(SEORecommendation.id == recommendation_id)
        )
        return self.session.scalar(stmt)
