import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaInMemoryUpload

from app.config.settings import settings

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

# Delete ALL docs from the service account Drive on cleanup.
# Docs are transferred to the share_email owner after creation, so the
# service account should never accumulate owned files.
_KEEP_LAST_N_DOCS = 0


class GoogleDocsService:
    """
    Upload rendered HTML proposals to Google Drive as native Google Docs.

    Authenticates via a service account JSON file. Both the Drive and Docs
    API clients are built once at __init__ time and reused across calls
    (the instance is meant to be a module-level singleton).

    Raises:
        FileNotFoundError: on construction if the credentials file is absent.
    """

    def __init__(self) -> None:
        cred_path = Path(settings.GOOGLE_SERVICE_ACCOUNT_FILE)
        if not cred_path.exists():
            raise FileNotFoundError(
                f"Google service account credentials not found at '{cred_path}'. "
                "Download the service account JSON from the Google Cloud Console "
                "and place it at that path."
            )

        credentials = service_account.Credentials.from_service_account_file(
            str(cred_path),
            scopes=_SCOPES,
        )

        # Build and cache both API clients (avoids repeated discovery fetches)
        self._drive = build(
            "drive", "v3", credentials=credentials, cache_discovery=False
        )
        self._docs = build(
            "docs", "v1", credentials=credentials, cache_discovery=False
        )

        logger.info("GoogleDocsService ready (credentials: %s)", cred_path)

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    def _cleanup_old_docs(self, keep_last_n: int = _KEEP_LAST_N_DOCS) -> int:
        """
        Delete older files from the service account Drive to free quota.

        Lists ALL files owned by the service account (not just Docs), sorted
        oldest-first, permanently deletes all but the ``keep_last_n``
        most-recent ones, and empties the trash to reclaim quota immediately.

        Args:
            keep_last_n: Number of recent files to preserve (default 0 = delete all).

        Returns:
            Number of files deleted.
        """
        deleted = 0
        try:
            # ── 1. Empty trash first (trashed files still consume quota) ──
            try:
                self._drive.files().emptyTrash().execute()
                logger.info("Drive trash emptied.")
            except HttpError as exc:
                logger.warning("Could not empty trash: %s", exc)

            # ── 2. Delete active files owned by the service account ──────
            response = (
                self._drive.files()
                .list(
                    q="'me' in owners",
                    orderBy="createdTime",
                    fields="files(id, name, createdTime)",
                    pageSize=1000,
                )
                .execute()
            )
            files: list[dict] = response.get("files", [])
            if keep_last_n == 0:
                to_delete = files
            elif len(files) > keep_last_n:
                to_delete = files[:-keep_last_n]
            else:
                to_delete = []

            for f in to_delete:
                try:
                    self._drive.files().delete(fileId=f["id"]).execute()
                    deleted += 1
                    logger.info(
                        "Deleted old file: '%s' (%s)", f["name"], f["id"]
                    )
                except HttpError as exc:
                    logger.warning(
                        "Could not delete file %s: %s", f["id"], exc
                    )

            logger.info(
                "Drive cleanup: deleted %d file(s), kept %d",
                deleted,
                len(files) - deleted,
            )
            return deleted

        except Exception as exc:
            logger.warning("Drive cleanup failed (non-fatal): %s", exc)
            return deleted

    def _build_media(self, html_content: str) -> MediaInMemoryUpload:
        """Create a fresh MediaInMemoryUpload from HTML bytes."""
        return MediaInMemoryUpload(
            html_content.encode("utf-8"),
            mimetype="text/html",
            resumable=False,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────

    def create_doc_from_html(
        self,
        html_content: str,
        title: str,
        share_email: str | None = None,
    ) -> str:
        """
        Upload HTML as a Google Doc and return its edit URL.

        If Drive's storage quota is exceeded on the first attempt, old docs
        are automatically cleaned up and the upload is retried once.

        Args:
            html_content: Fully rendered HTML string (from proposal_renderer).
            title:        Document title as it appears in Google Drive.
            share_email:  If provided, grants this address writer access.

        Returns:
            Google Docs edit URL:
            ``https://docs.google.com/document/d/{doc_id}/edit``

        Raises:
            HttpError: on any unrecoverable Drive/Docs API failure.
        """
        logger.info("Uploading Google Doc: title='%s'", title)

        file_metadata: dict = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",
        }
        if settings.GOOGLE_DOCS_FOLDER_ID:
            file_metadata["parents"] = [settings.GOOGLE_DOCS_FOLDER_ID]

        # ── Attempt 1 ────────────────────────────────────────────────────
        try:
            file = (
                self._drive.files()
                .create(
                    body=file_metadata,
                    media_body=self._build_media(html_content),
                    fields="id",
                )
                .execute()
            )
        except HttpError as exc:
            if _is_quota_error(exc):
                logger.warning(
                    "Drive storage quota exceeded — cleaning up old docs and retrying."
                )
                self._cleanup_old_docs()

                # ── Attempt 2 (after cleanup) ─────────────────────────
                file = (
                    self._drive.files()
                    .create(
                        body=file_metadata,
                        media_body=self._build_media(html_content),
                        fields="id",
                    )
                    .execute()
                )
                logger.info("Retry after cleanup succeeded.")
            else:
                raise

        doc_id: str = file["id"]
        logger.info("Google Doc created: id=%s", doc_id)

        if share_email:
            self._share_or_transfer(doc_id, share_email)

        edit_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        logger.info("Google Doc ready: %s", edit_url)
        return edit_url

    def _share_or_transfer(self, doc_id: str, share_email: str) -> None:
        """
        Attempt to transfer ownership of ``doc_id`` to ``share_email``.

        Ownership transfer permanently moves the file's storage cost from the
        service account to the recipient's Google Drive, solving the quota
        exhaustion problem.  If the transfer is rejected (e.g. the target is a
        Workspace account with external-share restrictions) we fall back to
        granting writer access instead.
        """
        try:
            self._drive.permissions().create(
                fileId=doc_id,
                body={
                    "type": "user",
                    "role": "owner",
                    "emailAddress": share_email,
                },
                transferOwnership=True,
                sendNotificationEmail=False,
            ).execute()
            logger.info(
                "Ownership of doc %s transferred to %s — storage now on recipient's quota",
                doc_id,
                share_email,
            )
        except HttpError as exc:
            logger.warning(
                "Ownership transfer to %s not permitted (%s) — falling back to writer access",
                share_email,
                exc.reason,
            )
            self._drive.permissions().create(
                fileId=doc_id,
                body={
                    "type": "user",
                    "role": "writer",
                    "emailAddress": share_email,
                },
                sendNotificationEmail=False,
            ).execute()
            logger.info("Shared doc %s with %s (writer)", doc_id, share_email)


# ── Module-level helper ───────────────────────────────────────────────────────

def _is_quota_error(exc: HttpError) -> bool:
    """Return True if the HttpError represents a Drive storage quota failure."""
    # exc.resp.status holds the integer HTTP status code (e.g. 403).
    # str(exc) includes the full Details JSON where 'storageQuotaExceeded' appears.
    return exc.resp.status == 403 and "storageQuotaExceeded" in str(exc)
