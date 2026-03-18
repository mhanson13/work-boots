# Deployment Configuration Contract

This document defines the canonical deploy-time naming contract for GitHub Actions, bootstrap scripting, and deployment runbooks.

## Naming Model

- Cloud-agnostic/technology-specific names are used for shared deploy concepts.
- Provider-specific names are used only where the value is inherently provider-bound.
- Runtime application env vars (for FastAPI/Next.js behavior) are documented separately and are not renamed here unless the app config is updated.

## Canonical Names

| Canonical name | Purpose | Example | Classification | Used in | Deprecated prior names |
|---|---|---|---|---|---|
| `OIDC_WORKLOAD_IDENTITY_PROVIDER` | OIDC workload identity provider resource used by deploy auth action | `projects/123456789012/locations/global/workloadIdentityPools/github-pool/providers/github-provider` | Cloud-agnostic/technology-specific | `.github/workflows/deploy-gke.yml`, `docs/gcp-github-actions-*.md`, bootstrap output | `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_WIF_PROVIDER` |
| `DEPLOY_SERVICE_ACCOUNT` | Deploy identity principal used by OIDC auth action | `work-boots-github-deployer@work-boots.iam.gserviceaccount.com` | Cloud-agnostic/technology-specific | `.github/workflows/deploy-gke.yml`, `docs/gcp-github-actions-*.md`, bootstrap output | `GCP_SERVICE_ACCOUNT_EMAIL`, `GCP_WIF_SERVICE_ACCOUNT` |
| `CONTAINER_REGISTRY_REGION` | Registry region used to build image URI | `us-central1` | Cloud-agnostic/technology-specific | `.github/workflows/deploy-gke.yml`, bootstrap inputs, deployment docs | `GAR_LOCATION` |
| `CONTAINER_REGISTRY_REPOSITORY` | Registry repository name used to build image URI | `work-boots` | Cloud-agnostic/technology-specific | `.github/workflows/deploy-gke.yml`, bootstrap inputs, deployment docs | `GAR_REPOSITORY` |
| `BUILD_SOURCE_DIR` | Build source staging URI passed to Cloud Build submit | `gs://work-boots-build-source/source` | Cloud-agnostic/technology-specific | `.github/workflows/deploy-gke.yml`, bootstrap inputs, deployment docs | `BUILD_SOURCE_BUCKET`, `GCS_SOURCE_STAGING_BUCKET` |
| `KUBERNETES_CLUSTER_NAME` | Target Kubernetes cluster name for deploy credentials | `work-boots-cluster` | Cloud-agnostic/technology-specific | `.github/workflows/deploy-gke.yml`, bootstrap optional inputs, deployment docs | `GKE_CLUSTER` |
| `KUBERNETES_CLUSTER_REGION` | Target Kubernetes cluster region | `us-central1` | Cloud-agnostic/technology-specific | `.github/workflows/deploy-gke.yml`, bootstrap optional inputs, deployment docs | `GKE_LOCATION` |
| `KUBERNETES_CLUSTER_MODE` | Kubernetes provisioning mode used by bootstrap cluster creation | `autopilot` | Cloud-agnostic/technology-specific | `scripts/bootstrap_gcp_github_actions.sh`, bootstrap docs | None (new canonical name) |
| `GCP_PROJECT_ID` | Google Cloud project identifier used by `gcloud` commands and image URI path | `work-boots` | Provider-specific | `.github/workflows/deploy-gke.yml` (literal), bootstrap inputs/docs | `PROJECT_ID` |

## Runtime Google Auth Variables (Intentionally Kept)

The backend runtime currently reads these names in `app/core/config.py` and related integration code:

- `GOOGLE_OIDC_CLIENT_ID`
- `GOOGLE_OIDC_CLIENT_SECRET`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`

These are intentionally unchanged in this pass to avoid runtime behavior changes.
