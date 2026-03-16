from __future__ import annotations

from dataclasses import dataclass
import time
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.models.seo_audit_finding import SEOAuditFinding
from app.models.seo_audit_page import SEOAuditPage
from app.models.seo_audit_run import SEOAuditRun
from app.models.seo_competitor_comparison_finding import SEOCompetitorComparisonFinding
from app.models.seo_competitor_comparison_run import SEOCompetitorComparisonRun
from app.models.seo_competitor_snapshot_page import SEOCompetitorSnapshotPage
from app.repositories.business_repository import BusinessRepository
from app.repositories.seo_audit_repository import SEOAuditRepository
from app.repositories.seo_competitor_repository import SEOCompetitorRepository
from app.schemas.seo_competitor import SEOCompetitorComparisonRunCreateRequest
from app.services.seo_finding_rules import FindingCategory, FindingSeverity


class SEOCompetitorComparisonNotFoundError(ValueError):
    pass


class SEOCompetitorComparisonValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SEOCompetitorComparisonResult:
    run: SEOCompetitorComparisonRun
    findings: list[SEOCompetitorComparisonFinding]


@dataclass(frozen=True)
class _ComparisonMetric:
    key: str
    title: str
    category: str
    higher_is_better: bool
    client_value: int
    competitor_value: int
    critical_delta_threshold: int


class SEOCompetitorComparisonService:
    def __init__(
        self,
        *,
        session: Session,
        business_repository: BusinessRepository,
        seo_audit_repository: SEOAuditRepository,
        seo_competitor_repository: SEOCompetitorRepository,
    ) -> None:
        self.session = session
        self.business_repository = business_repository
        self.seo_audit_repository = seo_audit_repository
        self.seo_competitor_repository = seo_competitor_repository

    def run_comparison(
        self,
        *,
        business_id: str,
        competitor_set_id: str,
        payload: SEOCompetitorComparisonRunCreateRequest,
        created_by_principal_id: str | None,
    ) -> SEOCompetitorComparisonResult:
        self._require_business(business_id)
        competitor_set = self.seo_competitor_repository.get_set_for_business(business_id, competitor_set_id)
        if competitor_set is None:
            raise SEOCompetitorComparisonNotFoundError("Competitor set not found")

        snapshot_run = self.seo_competitor_repository.get_snapshot_run_for_business(
            business_id,
            payload.snapshot_run_id,
        )
        if snapshot_run is None:
            raise SEOCompetitorComparisonNotFoundError("Competitor snapshot run not found")
        if snapshot_run.competitor_set_id != competitor_set.id:
            raise SEOCompetitorComparisonValidationError("Snapshot run does not belong to the target competitor set")
        if snapshot_run.site_id != competitor_set.site_id:
            raise SEOCompetitorComparisonValidationError("Snapshot run site does not match competitor set site")
        if snapshot_run.status != "completed":
            raise SEOCompetitorComparisonValidationError("Snapshot run must be completed before comparison")

        baseline_run = self._resolve_baseline_run(
            business_id=business_id,
            site_id=competitor_set.site_id,
            explicit_baseline_run_id=payload.baseline_audit_run_id,
            snapshot_client_run_id=snapshot_run.client_audit_run_id,
        )
        baseline_run_id = baseline_run.id if baseline_run is not None else None

        run = SEOCompetitorComparisonRun(
            id=str(uuid4()),
            business_id=business_id,
            site_id=competitor_set.site_id,
            competitor_set_id=competitor_set.id,
            snapshot_run_id=snapshot_run.id,
            baseline_audit_run_id=baseline_run_id,
            status="queued",
            total_findings=0,
            critical_findings=0,
            warning_findings=0,
            info_findings=0,
            created_by_principal_id=created_by_principal_id,
        )
        try:
            self.seo_competitor_repository.create_comparison_run(run)
            self.session.commit()
        except ValueError as exc:
            self.session.rollback()
            raise SEOCompetitorComparisonValidationError(str(exc)) from exc

        started = time.monotonic()
        run.status = "running"
        run.started_at = utc_now()
        self.seo_competitor_repository.save_comparison_run(run)
        self.session.commit()

        try:
            findings = self._generate_findings(
                business_id=business_id,
                run=run,
                baseline_run=baseline_run,
            )
            for finding in findings:
                self.seo_competitor_repository.add_comparison_finding(finding)

            run.total_findings = len(findings)
            run.critical_findings = sum(1 for item in findings if item.severity == FindingSeverity.CRITICAL)
            run.warning_findings = sum(1 for item in findings if item.severity == FindingSeverity.WARNING)
            run.info_findings = sum(1 for item in findings if item.severity == FindingSeverity.INFO)
            run.status = "completed"
            run.completed_at = utc_now()
            run.duration_ms = int((time.monotonic() - started) * 1000)
            run.error_summary = None
            self.seo_competitor_repository.save_comparison_run(run)
            self.session.commit()
            self.session.refresh(run)
            return SEOCompetitorComparisonResult(run=run, findings=findings)
        except Exception as exc:  # noqa: BLE001
            self.session.rollback()
            run.status = "failed"
            run.completed_at = utc_now()
            run.duration_ms = int((time.monotonic() - started) * 1000)
            run.error_summary = str(exc)[:1000]
            self.seo_competitor_repository.save_comparison_run(run)
            self.session.commit()
            raise SEOCompetitorComparisonValidationError("Deterministic comparison run failed") from exc

    def list_runs(self, *, business_id: str, competitor_set_id: str) -> list[SEOCompetitorComparisonRun]:
        self._require_business(business_id)
        competitor_set = self.seo_competitor_repository.get_set_for_business(business_id, competitor_set_id)
        if competitor_set is None:
            raise SEOCompetitorComparisonNotFoundError("Competitor set not found")
        return self.seo_competitor_repository.list_comparison_runs_for_business_set(
            business_id,
            competitor_set_id,
        )

    def get_run(self, *, business_id: str, comparison_run_id: str) -> SEOCompetitorComparisonRun:
        self._require_business(business_id)
        run = self.seo_competitor_repository.get_comparison_run_for_business(business_id, comparison_run_id)
        if run is None:
            raise SEOCompetitorComparisonNotFoundError("Competitor comparison run not found")
        return run

    def list_findings(
        self,
        *,
        business_id: str,
        comparison_run_id: str,
    ) -> list[SEOCompetitorComparisonFinding]:
        self.get_run(business_id=business_id, comparison_run_id=comparison_run_id)
        return self.seo_competitor_repository.list_comparison_findings_for_business_run(
            business_id,
            comparison_run_id,
        )

    def summarize_findings(
        self,
        *,
        findings: list[SEOCompetitorComparisonFinding],
    ) -> tuple[dict[str, int], dict[str, int]]:
        by_category = {
            FindingCategory.SEO: 0,
            FindingCategory.CONTENT: 0,
            FindingCategory.STRUCTURE: 0,
            FindingCategory.TECHNICAL: 0,
        }
        by_severity = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.WARNING: 0,
            FindingSeverity.INFO: 0,
        }
        for finding in findings:
            category = finding.category.strip().upper()
            severity = finding.severity.strip().upper()
            if category not in by_category:
                category = FindingCategory.TECHNICAL
            if severity not in by_severity:
                severity = FindingSeverity.INFO
            by_category[category] += 1
            by_severity[severity] += 1
        return by_category, by_severity

    def _generate_findings(
        self,
        *,
        business_id: str,
        run: SEOCompetitorComparisonRun,
        baseline_run: SEOAuditRun | None,
    ) -> list[SEOCompetitorComparisonFinding]:
        snapshot_pages = self.seo_competitor_repository.list_snapshot_pages_for_business_run(
            business_id,
            run.snapshot_run_id,
        )
        client_pages: list[SEOAuditPage] = []
        client_findings: list[SEOAuditFinding] = []
        if baseline_run is not None:
            client_pages = self.seo_audit_repository.list_pages_for_business_run(
                business_id,
                baseline_run.id,
            )
            client_findings = self.seo_audit_repository.list_findings_for_business_run(
                business_id,
                baseline_run.id,
            )

        metrics = self._build_metrics(
            client_pages=client_pages,
            client_findings=client_findings,
            snapshot_pages=snapshot_pages,
        )

        findings: list[SEOCompetitorComparisonFinding] = []
        for metric in metrics:
            severity, gap_direction, delta = self._classify_metric(metric)
            details = (
                f"Client={metric.client_value}, competitors={metric.competitor_value}, delta={delta}."
            )
            findings.append(
                SEOCompetitorComparisonFinding(
                    id=str(uuid4()),
                    business_id=run.business_id,
                    site_id=run.site_id,
                    competitor_set_id=run.competitor_set_id,
                    comparison_run_id=run.id,
                    finding_type=f"{metric.key}_gap",
                    category=metric.category,
                    severity=severity,
                    title=metric.title,
                    details=details,
                    rule_key=f"comparison_{metric.key}",
                    client_value=str(metric.client_value),
                    competitor_value=str(metric.competitor_value),
                    gap_direction=gap_direction,
                    evidence_json={"client": metric.client_value, "competitor": metric.competitor_value, "delta": delta},
                )
            )

        if baseline_run is None:
            findings.append(
                SEOCompetitorComparisonFinding(
                    id=str(uuid4()),
                    business_id=run.business_id,
                    site_id=run.site_id,
                    competitor_set_id=run.competitor_set_id,
                    comparison_run_id=run.id,
                    finding_type="missing_client_baseline",
                    category=FindingCategory.TECHNICAL,
                    severity=FindingSeverity.WARNING,
                    title="Missing client baseline audit",
                    details="No completed first-party audit run was available for baseline comparison.",
                    rule_key="comparison_missing_client_baseline",
                    client_value=None,
                    competitor_value=str(len(snapshot_pages)),
                    gap_direction="unknown",
                    evidence_json={"snapshot_page_count": len(snapshot_pages)},
                )
            )

        if not snapshot_pages:
            findings.append(
                SEOCompetitorComparisonFinding(
                    id=str(uuid4()),
                    business_id=run.business_id,
                    site_id=run.site_id,
                    competitor_set_id=run.competitor_set_id,
                    comparison_run_id=run.id,
                    finding_type="empty_competitor_snapshot",
                    category=FindingCategory.TECHNICAL,
                    severity=FindingSeverity.WARNING,
                    title="Competitor snapshot has no captured pages",
                    details="Snapshot run exists but no competitor pages were captured.",
                    rule_key="comparison_empty_snapshot",
                    client_value=str(len(client_pages)),
                    competitor_value="0",
                    gap_direction="unknown",
                    evidence_json={"client_page_count": len(client_pages)},
                )
            )

        return findings

    def _build_metrics(
        self,
        *,
        client_pages: list[SEOAuditPage],
        client_findings: list[SEOAuditFinding],
        snapshot_pages: list[SEOCompetitorSnapshotPage],
    ) -> list[_ComparisonMetric]:
        finding_counts: dict[str, int] = {}
        for finding in client_findings:
            key = (finding.finding_type or "").strip().lower()
            finding_counts[key] = finding_counts.get(key, 0) + 1

        competitor_missing_title = sum(1 for page in snapshot_pages if not (page.title or "").strip())
        competitor_missing_meta = sum(1 for page in snapshot_pages if not (page.meta_description or "").strip())
        competitor_missing_h1 = sum(1 for page in snapshot_pages if len(page.h1_json or []) == 0)
        competitor_thin_content = sum(1 for page in snapshot_pages if (page.word_count or 0) < 150)
        competitor_missing_canonical = sum(1 for page in snapshot_pages if not (page.canonical_url or "").strip())

        return [
            _ComparisonMetric(
                key="page_count",
                title="Page coverage gap",
                category=FindingCategory.STRUCTURE,
                higher_is_better=True,
                client_value=len(client_pages),
                competitor_value=len(snapshot_pages),
                critical_delta_threshold=5,
            ),
            _ComparisonMetric(
                key="missing_title",
                title="Missing title count gap",
                category=FindingCategory.SEO,
                higher_is_better=False,
                client_value=finding_counts.get("missing_title", 0),
                competitor_value=competitor_missing_title,
                critical_delta_threshold=3,
            ),
            _ComparisonMetric(
                key="missing_meta_description",
                title="Missing meta description count gap",
                category=FindingCategory.SEO,
                higher_is_better=False,
                client_value=finding_counts.get("missing_meta_description", 0),
                competitor_value=competitor_missing_meta,
                critical_delta_threshold=3,
            ),
            _ComparisonMetric(
                key="missing_h1",
                title="Missing H1 count gap",
                category=FindingCategory.STRUCTURE,
                higher_is_better=False,
                client_value=finding_counts.get("missing_h1", 0),
                competitor_value=competitor_missing_h1,
                critical_delta_threshold=3,
            ),
            _ComparisonMetric(
                key="thin_content",
                title="Thin content count gap",
                category=FindingCategory.CONTENT,
                higher_is_better=False,
                client_value=finding_counts.get("thin_content", 0),
                competitor_value=competitor_thin_content,
                critical_delta_threshold=3,
            ),
            _ComparisonMetric(
                key="missing_canonical",
                title="Missing canonical count gap",
                category=FindingCategory.TECHNICAL,
                higher_is_better=False,
                client_value=finding_counts.get("missing_canonical", 0),
                competitor_value=competitor_missing_canonical,
                critical_delta_threshold=2,
            ),
        ]

    def _classify_metric(self, metric: _ComparisonMetric) -> tuple[str, str, int]:
        delta = metric.client_value - metric.competitor_value
        if metric.higher_is_better:
            if delta > 0:
                return FindingSeverity.INFO, "client_leads", delta
            if delta < 0:
                if abs(delta) >= metric.critical_delta_threshold:
                    return FindingSeverity.CRITICAL, "client_trails", delta
                return FindingSeverity.WARNING, "client_trails", delta
            return FindingSeverity.INFO, "parity", delta

        # Lower is better for defect counts.
        if delta < 0:
            return FindingSeverity.INFO, "client_leads", delta
        if delta > 0:
            if delta >= metric.critical_delta_threshold:
                return FindingSeverity.CRITICAL, "client_trails", delta
            return FindingSeverity.WARNING, "client_trails", delta
        return FindingSeverity.INFO, "parity", delta

    def _resolve_baseline_run(
        self,
        *,
        business_id: str,
        site_id: str,
        explicit_baseline_run_id: str | None,
        snapshot_client_run_id: str | None,
    ) -> SEOAuditRun | None:
        selected_id = explicit_baseline_run_id or snapshot_client_run_id
        if selected_id is not None:
            run = self.seo_audit_repository.get_run_for_business(business_id, selected_id)
            if run is None:
                raise SEOCompetitorComparisonValidationError("Baseline audit run not found")
            if run.site_id != site_id:
                raise SEOCompetitorComparisonValidationError("Baseline audit run does not match competitor set site")
            if run.status != "completed":
                raise SEOCompetitorComparisonValidationError("Baseline audit run must be completed")
            return run

        return self.seo_audit_repository.get_latest_completed_run_for_business_site(business_id, site_id)

    def _require_business(self, business_id: str) -> None:
        business = self.business_repository.get(business_id)
        if business is None:
            raise SEOCompetitorComparisonNotFoundError("Business not found")
