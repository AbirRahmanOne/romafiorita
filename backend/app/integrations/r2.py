"""Cloudflare R2 upload signing seam.

Returns a signed PUT URL (direct browser upload) + the eventual public URL. Keys
are server-generated so clients can't choose paths. The default ``MockUploadSigner``
returns deterministic fake URLs; a real R2/S3 signer is a drop-in later.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

# Allowed image types + their file extensions.
ALLOWED_MIME = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}
_PUBLIC_BASE = "https://cdn.romafiorita.com"


@dataclass(frozen=True)
class SignedUpload:
    upload_url: str
    public_url: str
    key: str


def new_key(content_type: str) -> str:
    ext = ALLOWED_MIME[content_type]
    return f"uploads/{uuid.uuid4().hex}.{ext}"


class UploadSigner(Protocol):
    def sign_put(self, key: str, content_type: str) -> SignedUpload: ...


class MockUploadSigner:
    def sign_put(self, key: str, content_type: str) -> SignedUpload:
        return SignedUpload(
            upload_url=f"{_PUBLIC_BASE}/{key}?mock-signature",
            public_url=f"{_PUBLIC_BASE}/{key}",
            key=key,
        )


_signer: UploadSigner = MockUploadSigner()


def get_upload_signer() -> UploadSigner:
    return _signer
