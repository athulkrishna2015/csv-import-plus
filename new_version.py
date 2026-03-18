import json
import re
import sys
from pathlib import Path

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")


def _normalize_version(version: str) -> str:
    version = (version or "").strip()
    if version.startswith("v"):
        version = version[1:]
    if not _VERSION_RE.match(version):
        raise ValueError(
            "Version must follow <major>.<minor> or <major>.<minor>.<patch> "
            "(e.g., 2.6 or 2.6.1)."
        )
    return version


def read_manifest_version(addon_dir: str) -> str:
    manifest_file = Path(addon_dir) / "manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        for key in ("version", "human_version"):
            value = (manifest.get(key) or "").strip()
            if value:
                return value

    version_file = Path(addon_dir) / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()

    raise FileNotFoundError(
        f"No version found in {manifest_file} or {version_file}"
    )


def bump_version_string(current_version: str) -> str:
    normalized = _normalize_version(current_version)
    parts = normalized.split(".")
    if len(parts) == 2:
        major, minor = parts
        return f"{int(major)}.{int(minor) + 1}"
    major, minor, patch = parts
    return f"{int(major)}.{int(minor)}.{int(patch) + 1}"


def update_version(new_version: str, addon_dir: str) -> str:
    normalized = _normalize_version(new_version)

    version_file = Path(addon_dir) / "VERSION"
    if version_file.exists():
        version_file.write_text(normalized, encoding="utf-8")
        print(f"Updated {version_file}")

    manifest_file = Path(addon_dir) / "manifest.json"
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if "version" in manifest or "human_version" in manifest:
            if "version" in manifest:
                manifest["version"] = normalized
            if "human_version" in manifest:
                manifest["human_version"] = normalized
        else:
            manifest["version"] = normalized
        manifest_file.write_text(json.dumps(manifest, indent=4), encoding="utf-8")
        print(f"Updated {manifest_file}")

    return normalized


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python new_version.py <new_version> <addon_dir>")
        sys.exit(1)

    try:
        update_version(sys.argv[1], sys.argv[2])
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
