from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_CLOUD_LOGGING_SCOPE = "https://www.googleapis.com/auth/logging.read"
_CLOUD_LOGGING_ENTRIES_LIST_URL = "https://logging.googleapis.com/v2/entries:list"


class GoogleCloudLoggingADCError(ValueError):
    pass


class GoogleCloudLoggingAPIError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_status: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_status = error_status

    @property
    def is_permission_denied(self) -> bool:
        return self.status_code in {401, 403} or (self.error_status or "").upper() in {
            "PERMISSION_DENIED",
            "UNAUTHENTICATED",
        }

    @property
    def is_timeout(self) -> bool:
        if self.status_code in {408, 504}:
            return True
        status_upper = (self.error_status or "").upper()
        return status_upper in {"DEADLINE_EXCEEDED", "REQUEST_TIMEOUT"}

    @property
    def is_invalid_request(self) -> bool:
        if self.status_code in {400, 422}:
            return True
        return (self.error_status or "").upper() in {"INVALID_ARGUMENT", "FAILED_PRECONDITION"}


@dataclass(frozen=True)
class _GoogleErrorDetail:
    message: str
    status_code: int | None
    error_status: str | None


class GoogleCloudLoggingClient:
    def __init__(self, *, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds
        self._credentials: Any | None = None
        self._auth_request: Any | None = None

    def list_entries(
        self,
        *,
        project_id: str,
        filter_text: str,
        page_size: int,
        page_token: str | None = None,
        order_by: str = "timestamp desc",
    ) -> dict[str, Any]:
        normalized_project_id = project_id.strip()
        if not normalized_project_id:
            raise GoogleCloudLoggingADCError("Cloud Logging project id is required.")
        normalized_filter = filter_text.strip()
        if not normalized_filter:
            raise GoogleCloudLoggingAPIError("Cloud Logging filter is required.", status_code=400, error_status="INVALID_ARGUMENT")

        request_body: dict[str, Any] = {
            "resourceNames": [f"projects/{normalized_project_id}"],
            "filter": normalized_filter,
            "orderBy": order_by,
            "pageSize": int(page_size),
        }
        normalized_page_token = (page_token or "").strip()
        if normalized_page_token:
            request_body["pageToken"] = normalized_page_token

        return self._request_json(
            method="POST",
            url=_CLOUD_LOGGING_ENTRIES_LIST_URL,
            body=request_body,
        )

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        access_token = self._resolve_adc_access_token()
        payload = json.dumps(body, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        request = Request(
            url=url,
            method=method,
            data=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:  # noqa: S310
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = _extract_error_detail(exc)
            raise GoogleCloudLoggingAPIError(
                f"Cloud Logging request failed: {detail.message}",
                status_code=detail.status_code,
                error_status=detail.error_status,
            ) from exc
        except TimeoutError as exc:
            raise GoogleCloudLoggingAPIError(
                "Cloud Logging request timed out.",
                status_code=504,
                error_status="DEADLINE_EXCEEDED",
            ) from exc
        except URLError as exc:
            reason = exc.reason
            if isinstance(reason, (TimeoutError, socket.timeout)):
                raise GoogleCloudLoggingAPIError(
                    "Cloud Logging request timed out.",
                    status_code=504,
                    error_status="DEADLINE_EXCEEDED",
                ) from exc
            raise GoogleCloudLoggingAPIError("Cloud Logging endpoint unavailable.") from exc
        except Exception as exc:  # noqa: BLE001
            raise GoogleCloudLoggingAPIError("Cloud Logging request failed.") from exc

        if not raw.strip():
            return {}
        try:
            payload_obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GoogleCloudLoggingAPIError("Cloud Logging response is not valid JSON.") from exc
        if not isinstance(payload_obj, dict):
            raise GoogleCloudLoggingAPIError("Cloud Logging response payload is invalid.")
        return payload_obj

    def _resolve_adc_access_token(self) -> str:
        try:
            from google.auth import default as google_auth_default
            from google.auth.transport.requests import Request as GoogleAuthRequest
        except ImportError as exc:
            raise GoogleCloudLoggingADCError("google-auth dependency is required for Cloud Logging ADC access.") from exc

        try:
            if self._credentials is None:
                credentials, _ = google_auth_default(scopes=[_CLOUD_LOGGING_SCOPE])
                self._credentials = credentials
                self._auth_request = GoogleAuthRequest()
            credentials = self._credentials
            if credentials is None:
                raise GoogleCloudLoggingADCError("Unable to resolve Application Default Credentials.")
            if not credentials.valid or not getattr(credentials, "token", None):
                auth_request = self._auth_request or GoogleAuthRequest()
                credentials.refresh(auth_request)
            token = str(getattr(credentials, "token", "") or "").strip()
            if not token:
                raise GoogleCloudLoggingADCError("Application Default Credentials did not return an access token.")
            return token
        except GoogleCloudLoggingADCError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise GoogleCloudLoggingADCError(
                "Unable to authorize Cloud Logging request with Application Default Credentials."
            ) from exc


def _extract_error_detail(exc: HTTPError) -> _GoogleErrorDetail:
    status_code = exc.code if isinstance(exc.code, int) else None
    message = str(exc.reason or "request failed")
    error_status: str | None = None
    try:
        if exc.fp is None:
            return _GoogleErrorDetail(message=message, status_code=status_code, error_status=error_status)
        body = exc.fp.read().decode("utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return _GoogleErrorDetail(message=message, status_code=status_code, error_status=error_status)

    if not body.strip():
        return _GoogleErrorDetail(message=message, status_code=status_code, error_status=error_status)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return _GoogleErrorDetail(message=body.strip()[:256], status_code=status_code, error_status=error_status)
    if not isinstance(payload, dict):
        return _GoogleErrorDetail(message=message, status_code=status_code, error_status=error_status)

    error_payload = payload.get("error")
    if isinstance(error_payload, dict):
        code = error_payload.get("code")
        if isinstance(code, int):
            status_code = code
        parsed_message = str(error_payload.get("message") or "").strip()
        if parsed_message:
            message = parsed_message
        parsed_status = str(error_payload.get("status") or "").strip()
        if parsed_status:
            error_status = parsed_status
    else:
        parsed_message = str(payload.get("error_description") or payload.get("message") or "").strip()
        if parsed_message:
            message = parsed_message
    return _GoogleErrorDetail(message=message, status_code=status_code, error_status=error_status)
