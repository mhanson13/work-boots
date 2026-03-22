"use client";

import Link from "next/link";
import { useOperatorContext } from "../../components/useOperatorContext";
import { useAuth } from "../../components/AuthProvider";
import { PageContainer } from "../../components/layout/PageContainer";
import { SectionCard } from "../../components/layout/SectionCard";

export default function DashboardPage() {
  const context = useOperatorContext();
  const { principal } = useAuth();

  if (context.loading) {
    return <section className="panel">Loading dashboard...</section>;
  }
  if (context.error) {
    return <section className="panel">Error: {context.error}</section>;
  }

  const hasSites = context.sites.length > 0;
  const hasUnauditedSite = context.sites.some((site) => !site.last_audit_run_id);
  const hasCompletedAudit = context.sites.some(
    (site) => (site.last_audit_status || "").trim().toLowerCase() === "completed",
  );

  return (
    <PageContainer>
      <SectionCard>
        <h1>Dashboard</h1>
        <p>
          Business scope: <code>{context.businessId}</code>
        </p>
        <p>
          Tracked SEO sites: <strong>{context.sites.length}</strong>
        </p>
        {!hasSites ? <p className="hint warning">No sites configured yet. Start by adding your first site.</p> : null}
        {hasSites && hasUnauditedSite ? (
          <p className="hint warning">At least one site has not been audited yet. Run your first audit from Sites.</p>
        ) : null}
        {hasCompletedAudit ? (
          <p className="hint muted">Audit data is available. Next step: review recommendations.</p>
        ) : null}
      </SectionCard>

      <SectionCard>
        <h2>Operator Navigation</h2>
        <div className="link-row">
          <Link href="/sites">Sites</Link>
          <Link href="/audits">Audit Runs</Link>
          <Link href="/competitors">Competitor Intelligence</Link>
          <Link href="/recommendations">Recommendations</Link>
          <Link href="/automation">Automation Runs</Link>
          <Link href="/business-profile">Google Business Profile</Link>
        </div>
      </SectionCard>

      <SectionCard>
        <h2>Admin</h2>
        {principal?.role === "admin" ? (
          <p className="hint muted">
            Business administration is available. Open <Link href="/admin">Admin</Link> to manage principals and settings.
          </p>
        ) : (
          <p className="hint muted">Business administration is restricted to admin principals.</p>
        )}
      </SectionCard>
    </PageContainer>
  );
}
