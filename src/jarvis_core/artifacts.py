"""Content-addressed storage and safe retrieval for model-visible evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Artifact:
    uri: str
    digest: str
    media_type: str
    size: int
    preview: str


class ArtifactStore(Protocol):
    def put(self, content: str | bytes, media_type: str = "text/plain") -> Artifact: ...
    def get(self, uri: str) -> bytes: ...


def _payload(content: str | bytes) -> bytes:
    return content.encode("utf-8") if isinstance(content, str) else content


def _digest_from_uri(uri: str) -> str:
    prefix = "artifact://sha256/"
    if not uri.startswith(prefix):
        raise ValueError("unsupported artifact URI")
    digest = uri[len(prefix) :]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("invalid artifact URI")
    return digest


def _artifact(content: bytes, media_type: str) -> Artifact:
    digest = hashlib.sha256(content).hexdigest()
    return Artifact(
        uri=f"artifact://sha256/{digest}",
        digest=digest,
        media_type=media_type,
        size=len(content),
        preview=content[:240].decode("utf-8", errors="replace"),
    )


class MemoryArtifactStore:
    def __init__(self) -> None:
        self._items: dict[str, bytes] = {}

    def put(self, content: str | bytes, media_type: str = "text/plain") -> Artifact:
        payload = _payload(content)
        artifact = _artifact(payload, media_type)
        self._items[artifact.digest] = payload
        return artifact

    def get(self, uri: str) -> bytes:
        return self._items[_digest_from_uri(uri)]


class FileArtifactStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, content: str | bytes, media_type: str = "text/plain") -> Artifact:
        payload = _payload(content)
        artifact = _artifact(payload, media_type)
        path = self.root / artifact.digest
        if not path.exists():
            path.write_bytes(payload)
        return artifact

    def get(self, uri: str) -> bytes:
        return (self.root / _digest_from_uri(uri)).read_bytes()


class ArtifactResolver:
    """Bounded retrieval adapter suitable for exposing as a model tool."""

    def __init__(self, store: ArtifactStore, *, max_bytes: int = 64_000) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self.store = store
        self.max_bytes = max_bytes

    def read(self, uri: str, *, offset: int = 0, limit: int | None = None) -> dict[str, object]:
        if offset < 0:
            raise ValueError("offset must be non-negative")
        requested = self.max_bytes if limit is None else limit
        if requested < 1 or requested > self.max_bytes:
            raise ValueError("limit exceeds resolver bounds")
        payload = self.store.get(uri)
        chunk = payload[offset : offset + requested]
        return {
            "uri": uri,
            "offset": offset,
            "size": len(payload),
            "content": chunk.decode("utf-8", errors="replace"),
            "next_offset": offset + len(chunk) if offset + len(chunk) < len(payload) else None,
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
