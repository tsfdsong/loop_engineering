"""LoopEngine install operations + manifest IO."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ALLOWED_KINDS = frozenset(
    {"link-or-copy", "registry-write", "merge-json", "inject-markers"}
)


@dataclass
class Operation:
    id: str
    kind: str
    ownership: str = "managed"
    source: str | None = None
    destination: str | None = None
    merge_keys: list[str] | None = None
    registry: str | None = None
    key: str | None = None
    payload: Any = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}


@dataclass
class Manifest:
    schema_version: int
    product: str
    version: str
    installed_at: str
    central_root: str
    skill_names: list[str] = field(default_factory=list)
    components: dict[str, Any] = field(default_factory=dict)
    operations: list[Operation] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "product": self.product,
            "version": self.version,
            "installed_at": self.installed_at,
            "central_root": self.central_root,
            "skill_names": list(self.skill_names),
            "components": self.components,
            "operations": [
                op.to_dict() if isinstance(op, Operation) else op
                for op in self.operations
            ],
            "extras": self.extras,
        }


def validate_manifest(m: Manifest) -> None:
    if m.schema_version != 2:
        raise ValueError(f"schema_version must be 2, got {m.schema_version}")
    if m.product != "loopengine":
        raise ValueError(f"product must be loopengine, got {m.product}")
    if not m.version:
        raise ValueError("version required")
    if not m.central_root:
        raise ValueError("central_root required")
    if not isinstance(m.skill_names, list):
        raise ValueError("skill_names must be a list")
    for op in m.operations:
        kind = op.kind if isinstance(op, Operation) else op.get("kind")
        if kind not in ALLOWED_KINDS:
            raise ValueError(f"unsupported operation kind: {kind}")


def _op_from_dict(d: dict[str, Any]) -> Operation:
    return Operation(
        id=d["id"],
        kind=d["kind"],
        ownership=d.get("ownership", "managed"),
        source=d.get("source"),
        destination=d.get("destination"),
        merge_keys=d.get("merge_keys"),
        registry=d.get("registry"),
        key=d.get("key"),
        payload=d.get("payload"),
    )


def load_manifest(path: Path | str) -> Manifest:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    ops = [_op_from_dict(o) for o in data.get("operations", [])]
    m = Manifest(
        schema_version=int(data["schema_version"]),
        product=data["product"],
        version=data["version"],
        installed_at=data.get("installed_at", ""),
        central_root=data["central_root"],
        skill_names=list(data.get("skill_names", [])),
        components=dict(data.get("components", {})),
        operations=ops,
        extras=dict(data.get("extras", {})),
    )
    validate_manifest(m)
    return m


def save_manifest(path: Path | str, m: Manifest) -> None:
    validate_manifest(m)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(m.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def _link_or_copy(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        if dst.is_symlink() or dst.is_file():
            dst.unlink()
        else:
            shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.symlink(src, dst, target_is_directory=src.is_dir())
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def apply_operation(op: Operation) -> None:
    if op.kind == "link-or-copy":
        if not op.source or not op.destination:
            raise ValueError("link-or-copy requires source and destination")
        _link_or_copy(Path(op.source).expanduser(), Path(op.destination).expanduser())
        return
    if op.kind in {"registry-write", "merge-json", "inject-markers"}:
        raise NotImplementedError(
            f"{op.kind} apply is implemented by adapters / later ops helpers"
        )
    raise ValueError(f"unknown kind: {op.kind}")


def revert_operation(op: Operation) -> None:
    if op.ownership != "managed":
        return
    if op.kind == "link-or-copy":
        if not op.destination:
            return
        dst = Path(op.destination).expanduser()
        if dst.is_symlink() or dst.is_file():
            dst.unlink(missing_ok=True)
        elif dst.is_dir():
            shutil.rmtree(dst)
        return
    if op.kind in {"registry-write", "merge-json", "inject-markers"}:
        raise NotImplementedError(
            f"{op.kind} revert is implemented by adapters / later ops helpers"
        )
    raise ValueError(f"unknown kind: {op.kind}")
