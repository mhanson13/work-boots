import { expect, test } from "@playwright/test";

const BUSINESS_ID = "biz-1";
const SITE_ID = "site-1";
const PRIMARY_RECOMMENDATION_ID = "rec-smoke-1";
const PRIMARY_RECOMMENDATION_TITLE = "Fix title tag duplication";
const SECONDARY_RECOMMENDATION_ID = "rec-smoke-2";
const SECONDARY_RECOMMENDATION_TITLE = "Refresh internal links";
const API_BASE_URL = "http://127.0.0.1:8000";

function buildRecommendation(input: {
  id: string;
  title: string;
  status: string;
  decisionReason?: string | null;
}) {
  return {
    id: input.id,
    business_id: BUSINESS_ID,
    site_id: SITE_ID,
    recommendation_run_id: "rec-run-1",
    audit_run_id: null,
    comparison_run_id: null,
    status: input.status,
    category: "SEO",
    severity: "warning",
    priority_score: 88,
    priority_band: "high",
    effort_bucket: "small",
    title: input.title,
    rationale: "Keep titles aligned with target keyword intent.",
    decision_reason: input.decisionReason ?? null,
    created_at: "2026-03-20T00:00:00Z",
    updated_at: "2026-03-20T00:00:00Z",
  };
}

test("recommendations queue smoke flow keeps route context and supports basic action flow", async ({ page }) => {
  let primaryRecommendationStatus = "open";
  let primaryRecommendationDecisionReason: string | null = null;
  const recommendationListQueryLog: string[] = [];
  const expectedQueueQuery = "status=open&sort_by=created_at&sort_order=asc&page=2&page_size=50";

  await page.addInitScript((principalBusinessId: string) => {
    window.sessionStorage.setItem("mbsrn.operator.access_token", "smoke-access-token");
    window.sessionStorage.setItem(
      "mbsrn.operator.principal",
      JSON.stringify({
        business_id: principalBusinessId,
        principal_id: "principal-smoke-1",
        display_name: "Smoke Operator",
        role: "admin",
        is_active: true,
      }),
    );
  }, BUSINESS_ID);

  await page.route(`${API_BASE_URL}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const pathname = url.pathname;
    const method = request.method();

    if (pathname === `/api/businesses/${BUSINESS_ID}/seo/sites` && method === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [
            {
              id: SITE_ID,
              business_id: BUSINESS_ID,
              display_name: "Smoke Test Site",
              base_url: "https://example.com",
              normalized_domain: "example.com",
              is_active: true,
              is_primary: true,
              last_audit_run_id: null,
              last_audit_status: null,
              last_audit_completed_at: null,
            },
          ],
          total: 1,
        }),
      });
      return;
    }

    if (pathname === `/api/businesses/${BUSINESS_ID}/seo/sites/${SITE_ID}/recommendations` && method === "GET") {
      recommendationListQueryLog.push(url.searchParams.toString());
      const statusFilter = url.searchParams.get("status") || "";

      const filteredItem =
        statusFilter === "open" && primaryRecommendationStatus !== "open"
          ? buildRecommendation({
              id: SECONDARY_RECOMMENDATION_ID,
              title: SECONDARY_RECOMMENDATION_TITLE,
              status: "open",
            })
          : buildRecommendation({
              id: PRIMARY_RECOMMENDATION_ID,
              title: PRIMARY_RECOMMENDATION_TITLE,
              status: primaryRecommendationStatus,
              decisionReason: primaryRecommendationDecisionReason,
            });

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [filteredItem],
          total: 51,
          filtered_summary: {
            total: 51,
            open: 51,
            accepted: 0,
            dismissed: 0,
            high_priority: 51,
          },
        }),
      });
      return;
    }

    if (
      pathname ===
        `/api/businesses/${BUSINESS_ID}/seo/sites/${SITE_ID}/recommendations/${PRIMARY_RECOMMENDATION_ID}` &&
      method === "GET"
    ) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(
          buildRecommendation({
            id: PRIMARY_RECOMMENDATION_ID,
            title: PRIMARY_RECOMMENDATION_TITLE,
            status: primaryRecommendationStatus,
            decisionReason: primaryRecommendationDecisionReason,
          }),
        ),
      });
      return;
    }

    if (
      pathname ===
        `/api/businesses/${BUSINESS_ID}/seo/sites/${SITE_ID}/recommendations/${PRIMARY_RECOMMENDATION_ID}` &&
      method === "PATCH"
    ) {
      const payloadText = request.postData();
      const payload = payloadText ? (JSON.parse(payloadText) as { status?: string; note?: string | null }) : {};
      if (payload.status === "accepted" || payload.status === "dismissed") {
        primaryRecommendationStatus = payload.status;
      }
      primaryRecommendationDecisionReason = typeof payload.note === "string" ? payload.note : null;

      await new Promise((resolve) => setTimeout(resolve, 250));

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(
          buildRecommendation({
            id: PRIMARY_RECOMMENDATION_ID,
            title: PRIMARY_RECOMMENDATION_TITLE,
            status: primaryRecommendationStatus,
            decisionReason: primaryRecommendationDecisionReason,
          }),
        ),
      });
      return;
    }

    await route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Not found in smoke mock." }),
    });
  });

  await page.goto("/");
  await expect(page).toHaveURL(/\/dashboard$/);

  await page.goto("/recommendations?status=open&sort=oldest&page=2&page_size=50");

  await expect(page.getByRole("heading", { name: "Recommendation Workflow" })).toBeVisible({ timeout: 10000 });
  await expect(page.locator("#recommendation-filter-status")).toHaveValue("open");
  await expect(page.locator("#recommendation-sort")).toHaveValue("oldest");
  await expect(page.locator("#recommendation-page-size")).toHaveValue("50");
  await expect(page.getByText("Page 2 of 2")).toBeVisible();
  await expect(page.getByText(PRIMARY_RECOMMENDATION_TITLE)).toBeVisible();

  await page.getByText(PRIMARY_RECOMMENDATION_TITLE).click();
  await expect(page).toHaveURL(
    /\/recommendations\/rec-smoke-1\?site_id=site-1&status=open&sort=oldest&page=2&page_size=50$/,
  );

  await expect(page.getByRole("heading", { name: "Recommendation Detail" })).toBeVisible();
  await expect(page.getByText("Status: open")).toBeVisible();

  await page.getByRole("button", { name: "Accept" }).click();
  await expect(page.getByText("Status: accepted")).toBeVisible();
  await expect(page.getByText("Recommendation marked as accepted.")).toBeVisible();

  await page.getByRole("link", { name: "Back to Recommendations" }).click();

  await expect(page).toHaveURL(/\/recommendations\?status=open&sort=oldest&page=2&page_size=50$/);
  await expect(page.locator("#recommendation-filter-status")).toHaveValue("open");
  await expect(page.locator("#recommendation-sort")).toHaveValue("oldest");
  await expect(page.locator("#recommendation-page-size")).toHaveValue("50");
  await expect(page.getByText("Page 2 of 2")).toBeVisible();
  await expect(page.getByText(SECONDARY_RECOMMENDATION_TITLE)).toBeVisible();

  expect(recommendationListQueryLog.length).toBeGreaterThanOrEqual(2);
  for (const query of recommendationListQueryLog) {
    expect(query).toBe(expectedQueueQuery);
  }
});
