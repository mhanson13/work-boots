# GCP Workload Identity for API ADC

## Purpose
The admin in-app Cloud Logging query depends on runtime Application Default Credentials (ADC) from GKE Workload Identity.

This document defines the required wiring and the runtime checks for diagnosing ADC failures.

## Required Wiring

1. API deployment must run with Kubernetes service account (KSA):
- `mbsrn-api`

2. KSA must be mapped to a Google service account (GSA):
- annotation key: `iam.gke.io/gcp-service-account`
- annotation value: `<RUNTIME_GSA_EMAIL>`

3. Runtime project scope must be configured:
- `GCP_PROJECT_ID`

## Required IAM Grants

Grant KSA impersonation on the runtime GSA:

```bash
gcloud iam service-accounts add-iam-policy-binding <RUNTIME_GSA_EMAIL> \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:<PROJECT_ID>.svc.id.goog[<NAMESPACE>/mbsrn-api]" \
  --project <PROJECT_ID>
```

Grant Cloud Logging read permission to the runtime GSA:

```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member "serviceAccount:<RUNTIME_GSA_EMAIL>" \
  --role "roles/logging.viewer"
```

## Cluster Verification

Verify deployment KSA:

```bash
kubectl -n <NAMESPACE> get deploy mbsrn-api \
  -o jsonpath='{.spec.template.spec.serviceAccountName}{"\n"}'
```

Verify KSA annotation:

```bash
kubectl -n <NAMESPACE> get sa mbsrn-api \
  -o jsonpath='{.metadata.annotations.iam\.gke\.io/gcp-service-account}{"\n"}'
```

Verify runtime env:

```bash
kubectl -n <NAMESPACE> exec deploy/mbsrn-api -- sh -c 'env | egrep "GCP_PROJECT_ID"'
```

Run the in-repo preflight helper:

```bash
python scripts/verify_gcp_logs_wiring.py
python scripts/verify_gcp_logs_wiring.py --cluster --namespace <NAMESPACE> --project-id <PROJECT_ID> --gsa-email <RUNTIME_GSA_EMAIL>
```

## Runtime ADC Diagnostic Endpoint

Admin-only diagnostic endpoint:

- `GET /admin/runtime/adc-check`

Response:

```json
{
  "adc_available": true,
  "project_id": "mbsrn-prod",
  "error": null
}
```

Notes:
- Endpoint never returns token material.
- If ADC is unavailable, endpoint returns `adc_available=false` with a bounded error message.
- Local development without ADC is expected to return `adc_available=false`.
- Deployment model is ADC-native only; do not wire `GOOGLE_APPLICATION_CREDENTIALS` for this feature.

## Common Failure Modes

1. `serviceAccountName` mismatch
- Deployment is not using `mbsrn-api`.

2. Missing KSA annotation
- `iam.gke.io/gcp-service-account` not set on `mbsrn-api`.

3. Missing `roles/iam.workloadIdentityUser`
- GSA does not allow KSA impersonation.

4. Missing `roles/logging.viewer`
- ADC exists, but Cloud Logging query fails with permission denied.

5. Missing `GCP_PROJECT_ID`
- Log query feature is not configured for a project scope.

6. Invalid `GCP_PROJECT_ID`
- Cloud Logging API returns project/resource-scope configuration failures.

Error classes surfaced by logs query route:

- `503` ADC failure: Workload Identity credentials could not be resolved/refreshed.
- `503` config failure: project env missing/invalid for Cloud Logging scope.
- `502` permission failure: runtime GSA authenticated but missing Cloud Logging read permission.
