import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class LoadedDocument(BaseModel):
    title: str
    source_type: str  # 'podcast', 'newsletter', etc.
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None
    external_id: Optional[str] = None
    content: str
    content_hash: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


def normalize_whitespace(text: str) -> str:
    """Normalize text whitespace while strictly preserving paragraph boundaries."""
    if not text:
        return ""
    # Standardize newline characters
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces and tabs with standard space
    text = text.replace("\xa0", " ").replace("\t", " ")
    # Collapse multiple inline spaces within each line
    lines = [re.sub(r" [ ]+", " ", line).strip() for line in text.split("\n")]
    # Reassemble and collapse 3+ consecutive newlines to double newline (\n\n)
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def compute_content_hash(text: str) -> str:
    """Generate deterministic SHA-256 hash of normalized text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_datetime(val: Any) -> Optional[datetime]:
    if not val:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    try:
        dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def make_json_serializable(val: Any) -> Any:
    """Recursively convert dates, datetimes, and complex types to JSON-safe primitives."""
    import datetime
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    elif isinstance(val, dict):
        return {str(k): make_json_serializable(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [make_json_serializable(x) for x in val]
    return val


def load_markdown(path: Path, base_dir: Optional[Path] = None) -> LoadedDocument:
    raw = path.read_text(encoding="utf-8")
    meta: Dict[str, Any] = {}
    content = raw

    # Check for YAML frontmatter
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            content = parts[2]
            try:
                import yaml
                parsed_fm = yaml.safe_load(fm_text)
                if isinstance(parsed_fm, dict):
                    meta = parsed_fm
            except Exception:
                # Fallback simple line-by-line parsing
                for line in fm_text.strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip().lower()] = v.strip().strip("\"'")

    normalized_content = normalize_whitespace(content)

    # Determine relative path for source provenance
    if base_dir:
        try:
            rel_path = path.relative_to(base_dir).as_posix()
        except Exception:
            rel_path = path.as_posix()
    elif "episodes" in path.parts:
        idx = path.parts.index("episodes")
        rel_path = "/".join(path.parts[idx:])
    else:
        rel_path = path.as_posix()

    meta["relative_path"] = rel_path

    # Extract metadata fields
    title = meta.get("title") or path.stem.replace("_", " ").replace("-", " ").title()
    if len(title) > 255:
        title = title[:252] + "..."

    guest = meta.get("guest")
    if guest:
        meta["guest"] = guest

    source_type = str(meta.get("source_type", "podcast")).lower()
    source_url = meta.get("youtube_url") or meta.get("source_url")
    published_at = parse_datetime(meta.get("publish_date") or meta.get("published_at"))
    external_id = str(
        meta.get("video_id")
        or meta.get("external_id")
        or (path.parent.name if path.name == "transcript.md" else path.stem)
    )

    clean_meta = make_json_serializable(meta)

    return LoadedDocument(
        title=title,
        source_type=source_type,
        source_url=source_url,
        published_at=published_at,
        external_id=external_id,
        content=normalized_content,
        content_hash=compute_content_hash(normalized_content),
        metadata=clean_meta,
    )


def load_txt(path: Path, base_dir: Optional[Path] = None) -> LoadedDocument:
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    meta: Dict[str, Any] = {}
    content_lines = []
    in_headers = True

    header_keys = {
        "title",
        "guest",
        "source-type",
        "source_type",
        "source-url",
        "source_url",
        "published-at",
        "published_at",
        "external-id",
        "external_id",
        "disclaimer",
    }

    for line in lines:
        if in_headers and ":" in line:
            prefix = line.split(":", 1)[0].strip().lower()
            if prefix in header_keys:
                k, v = line.split(":", 1)
                clean_k = k.strip().lower().replace("-", "_")
                meta[clean_k] = v.strip().strip("\"'")
                continue
        in_headers = False
        content_lines.append(line)

    content = "\n".join(content_lines)
    normalized_content = normalize_whitespace(content)

    if base_dir:
        try:
            rel_path = path.relative_to(base_dir).as_posix()
        except Exception:
            rel_path = path.as_posix()
    else:
        rel_path = path.as_posix()
    meta["relative_path"] = rel_path

    title = meta.get("title") or path.stem.replace("_", " ").replace("-", " ").title()
    if len(title) > 255:
        title = title[:252] + "..."
    source_type = meta.get("source_type", "newsletter").lower()
    source_url = meta.get("source_url")
    published_at = parse_datetime(meta.get("published_at"))
    external_id = meta.get("external_id") or path.stem

    return LoadedDocument(
        title=title,
        source_type=source_type,
        source_url=source_url,
        published_at=published_at,
        external_id=external_id,
        content=normalized_content,
        content_hash=compute_content_hash(normalized_content),
        metadata=meta,
    )


def load_json(path: Path, base_dir: Optional[Path] = None) -> LoadedDocument:
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = data.get("metadata", {})

    content = data.get("content", "")
    normalized_content = normalize_whitespace(content)

    if base_dir:
        try:
            rel_path = path.relative_to(base_dir).as_posix()
        except Exception:
            rel_path = path.as_posix()
    else:
        rel_path = path.as_posix()
    meta["relative_path"] = rel_path

    title = data.get("title") or meta.get("title") or path.stem.replace("_", " ").replace("-", " ").title()
    if len(title) > 255:
        title = title[:252] + "..."
    source_type = data.get("source_type", meta.get("source_type", "podcast")).lower()
    source_url = data.get("source_url", meta.get("source_url"))
    published_at = parse_datetime(data.get("published_at", meta.get("published_at")))
    external_id = data.get("external_id", meta.get("external_id")) or path.stem

    return LoadedDocument(
        title=title,
        source_type=source_type,
        source_url=source_url,
        published_at=published_at,
        external_id=external_id,
        content=normalized_content,
        content_hash=compute_content_hash(normalized_content),
        metadata=meta,
    )


def load_file(path: Path, base_dir: Optional[Path] = None) -> LoadedDocument:
    suffix = path.suffix.lower()
    if suffix == ".md":
        return load_markdown(path, base_dir=base_dir)
    elif suffix == ".txt":
        return load_txt(path, base_dir=base_dir)
    elif suffix == ".json":
        return load_json(path, base_dir=base_dir)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def load_directory(dir_path: Path, recursive: bool = True) -> List[LoadedDocument]:
    if not dir_path.exists():
        return []

    # If this is the ChatPRD repository with an 'episodes' subdirectory, prioritize episodes
    episodes_dir = dir_path / "episodes"
    target_dir = episodes_dir if episodes_dir.is_dir() else dir_path

    docs = []
    ignored_patterns = {".git", "node_modules", "__pycache__", ".pytest_cache", "index"}
    ignored_filenames = {"readme.md", "claude.md", "license", "contributing.md"}

    patterns = ("**/*.md", "**/*.txt", "**/*.json") if recursive else ("*.md", "*.txt", "*.json")
    seen_paths = set()

    for pattern in patterns:
        for file_path in sorted(target_dir.glob(pattern)):
            if file_path in seen_paths:
                continue
            seen_paths.add(file_path)

            # Skip ignored directories and repo meta files
            parts_lower = {p.lower() for p in file_path.parts}
            if any(ign in parts_lower for ign in ignored_patterns):
                continue
            if file_path.name.lower() in ignored_filenames:
                continue

            try:
                doc = load_file(file_path, base_dir=dir_path)
                # Ensure document has non-empty content
                if doc.content:
                    docs.append(doc)
            except Exception:
                pass

    return docs
