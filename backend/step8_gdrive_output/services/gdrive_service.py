"""Google Drive API service providing folder management and Google Document creation."""
import json
import time
from typing import Any, Dict, List, Optional
import urllib.parse

import httpx

from backend.common.logging.logger import logger
from backend.step6_mcp.google.auth import refresh_access_token_if_needed
from backend.step8_gdrive_output.config.gdrive_settings import Step8Settings, get_step8_settings
from backend.step8_gdrive_output.exceptions import GoogleDriveAPIError

GDRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GDRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"


class GoogleDriveService:
    """Interacts with Google Drive API v3 to manage folders and upload Google Documents."""

    def __init__(self, settings: Optional[Step8Settings] = None):
        self.settings = settings or get_step8_settings()

    def _get_headers(self) -> Dict[str, str]:
        """Obtain active OAuth bearer token and construct HTTP authorization headers."""
        token = refresh_access_token_if_needed()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        content: Optional[bytes] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """Execute HTTP request against Google Drive API with automatic bounded retries."""
        req_timeout = timeout or self.settings.timeout_seconds
        base_headers = self._get_headers()
        if headers:
            base_headers.update(headers)

        last_exc: Optional[Exception] = None
        for attempt in range(1, self.settings.max_retries + 1):
            try:
                with httpx.Client(timeout=req_timeout) as client:
                    resp = client.request(
                        method=method,
                        url=url,
                        headers=base_headers,
                        params=params,
                        json=json_data,
                        content=content,
                    )

                # Retry on rate limit (429) or transient Google server error (500, 502, 503, 504)
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < self.settings.max_retries:
                    wait_time = (self.settings.retry_backoff_factor ** attempt)
                    logger.warning(
                        f"Google Drive API returned status {resp.status_code}. Retrying in {wait_time:.1f}s (attempt {attempt})..."
                    )
                    time.sleep(wait_time)
                    # Refresh token in case it expired during backoff
                    base_headers = self._get_headers()
                    if headers:
                        base_headers.update(headers)
                    continue

                return resp

            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                if attempt < self.settings.max_retries:
                    wait_time = (self.settings.retry_backoff_factor ** attempt)
                    logger.warning(f"Google Drive network error: {exc}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                raise GoogleDriveAPIError("network_request", f"Network error after {attempt} attempts: {exc}")

        if last_exc:
            raise GoogleDriveAPIError("network_request", f"Failed after retries: {last_exc}")
        raise GoogleDriveAPIError("network_request", "Max retries exceeded.")

    def find_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Search for an existing folder by exact name and optional parent folder.

        Returns folder dict if found, else None.
        """
        escaped_name = name.replace("'", "\\'")
        query_parts = [
            f"name = '{escaped_name}'",
            "mimeType = 'application/vnd.google-apps.folder'",
            "trashed = false",
        ]
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")

        query = " and ".join(query_parts)
        params = {
            "q": query,
            "fields": "files(id, name, mimeType, webViewLink, parents)",
            "pageSize": 5,
        }

        resp = self._request_with_retry("GET", f"{GDRIVE_API_BASE}/files", params=params)
        if resp.status_code != 200:
            raise GoogleDriveAPIError("find_folder", resp.text, resp.status_code)

        files = resp.json().get("files", [])
        if files:
            return files[0]
        return None

    def create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new folder in Google Drive.

        Returns the created folder metadata including 'id' and 'webViewLink'.
        """
        metadata: Dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        params = {"fields": "id, name, mimeType, webViewLink, parents"}
        resp = self._request_with_retry(
            "POST",
            f"{GDRIVE_API_BASE}/files",
            params=params,
            json_data=metadata,
        )

        if resp.status_code not in (200, 201):
            raise GoogleDriveAPIError("create_folder", resp.text, resp.status_code)

        return resp.json()

    def get_or_create_folder(
        self,
        name: str,
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Idempotently find an existing folder or create it if missing."""
        existing = self.find_folder(name=name, parent_id=parent_id)
        if existing:
            return existing
        return self.create_folder(name=name, parent_id=parent_id)

    def create_google_document(
        self,
        title: str,
        content: str,
        folder_id: str,
    ) -> Dict[str, Any]:
        """Upload content as a native Google Document inside the specified folder.

        Uses multipart upload to convert text into application/vnd.google-apps.document.
        Returns document metadata dict containing 'id' and 'webViewLink'.
        """
        metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
            "parents": [folder_id],
        }

        boundary = "===============ESTD_BOUNDARY_SEP=="
        crlf = "\r\n"

        # Construct multipart body
        meta_json = json.dumps(metadata)
        body = (
            f"--{boundary}{crlf}"
            f"Content-Type: application/json; charset=UTF-8{crlf}{crlf}"
            f"{meta_json}{crlf}"
            f"--{boundary}{crlf}"
            f"Content-Type: text/plain; charset=UTF-8{crlf}{crlf}"
            f"{content}{crlf}"
            f"--{boundary}--{crlf}"
        ).encode("utf-8")

        headers = {
            "Content-Type": f"multipart/related; boundary={boundary}",
        }
        params = {
            "uploadType": "multipart",
            "fields": "id, name, mimeType, webViewLink, parents, createdTime",
        }

        resp = self._request_with_retry(
            "POST",
            f"{GDRIVE_UPLOAD_BASE}/files",
            headers=headers,
            params=params,
            content=body,
        )

        if resp.status_code not in (200, 201):
            raise GoogleDriveAPIError("create_google_document", resp.text, resp.status_code)

        data = resp.json()
        doc_id = data.get("id")
        doc_url = data.get("webViewLink") or f"https://docs.google.com/document/d/{doc_id}/edit"
        data["webViewLink"] = doc_url

        # PART Q: Verify document parent ID placement; move if not properly parented
        parents = data.get("parents") or []
        if folder_id not in parents:
            logger.warning(
                f"Document '{doc_id}' created without required parent '{folder_id}' (parents={parents}). Moving..."
            )
            data = self.move_file(doc_id, add_parents=folder_id)
            data["webViewLink"] = doc_url

        return data

    def move_file(
        self,
        file_id: str,
        add_parents: str,
        remove_parents: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Move or reparent a file or folder in Google Drive.

        Args:
            file_id: The ID of the file/folder to move.
            add_parents: Comma-separated list of parent IDs to add.
            remove_parents: Optional comma-separated list of parent IDs to remove.
                           If not specified, all existing parents (except add_parents) are removed.
        """
        params: Dict[str, Any] = {
            "addParents": add_parents,
            "fields": "id, name, mimeType, webViewLink, parents",
        }
        if remove_parents is not None:
            if remove_parents:
                params["removeParents"] = remove_parents
        else:
            try:
                meta = self.get_file_metadata(file_id)
                current = meta.get("parents", [])
                to_remove = [p for p in current if p != add_parents]
                if to_remove:
                    params["removeParents"] = ",".join(to_remove)
            except Exception as exc:
                logger.warning(f"Could not inspect existing parents for '{file_id}' during move: {exc}")

        resp = self._request_with_retry(
            "PATCH",
            f"{GDRIVE_API_BASE}/files/{file_id}",
            params=params,
        )
        if resp.status_code not in (200, 201):
            raise GoogleDriveAPIError("move_file", resp.text, resp.status_code)
        return resp.json()

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Retrieve metadata for an existing Google Drive file or document."""
        params = {"fields": "id, name, mimeType, webViewLink, parents, trashed"}
        resp = self._request_with_retry("GET", f"{GDRIVE_API_BASE}/files/{file_id}", params=params)
        if resp.status_code != 200:
            raise GoogleDriveAPIError("get_file_metadata", resp.text, resp.status_code)
        return resp.json()

    def search_files(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for files in Google Drive matching query."""
        params = {
            "q": query,
            "fields": "files(id, name, mimeType, webViewLink)",
            "pageSize": limit,
        }
        resp = self._request_with_retry("GET", f"{GDRIVE_API_BASE}/files", params=params)
        if resp.status_code != 200:
            raise GoogleDriveAPIError("search_files", resp.text, resp.status_code)
        return resp.json().get("files", [])

    def update_file_metadata(
        self,
        file_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update file or folder metadata (e.g. rename) in Google Drive."""
        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        params = {"fields": "id, name, mimeType, webViewLink, parents"}
        resp = self._request_with_retry(
            "PATCH",
            f"{GDRIVE_API_BASE}/files/{file_id}",
            params=params,
            json_data=body,
        )
        if resp.status_code not in (200, 201):
            raise GoogleDriveAPIError("update_file_metadata", resp.text, resp.status_code)
        return resp.json()

    def delete_file(self, file_id: str) -> bool:
        """Permanently delete a file or document from Google Drive."""
        resp = self._request_with_retry("DELETE", f"{GDRIVE_API_BASE}/files/{file_id}")
        if resp.status_code not in (200, 204):
            if resp.status_code == 404:
                return True
            raise GoogleDriveAPIError("delete_file", resp.text, resp.status_code)
        return True

