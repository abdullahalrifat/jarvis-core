"""Content-addressed storage for large model-visible evidence."""

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


def _artifact(content: bytes, media_type: str) -> Artifact:
    digest = hashlib.sha256(content).hexdigest()
    preview = content[:240].decode("utf-8", errors="replace")
    return Artifact(
        uri=f"artifact://sha256/{digest}",
        digest=digest,
        media_type=media_type,
        size=len(content),
        preview=preview,
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
        digest = uri.rsplit("/", 1)[-1]
        return self._items[digest]


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
        digest = uri.rsplit("/", 1)[-1]
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            raise ValueError("invalid artifact URI")
        return (self.root / digest).read_bytes()
