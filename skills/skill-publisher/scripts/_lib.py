"""
skill-publisher 共享库：配置读取、API 客户端、技能打包与本地预校验。
复用平台 validate_service 的校验规则（纯函数子集），不依赖 FastAPI/数据库。
"""

from __future__ import annotations

import configparser
import io
import json
import os
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

# ── 常量 ──────────────────────────────────────────────

CREDENTIALS_FILE = Path.home() / ".ai-hub" / "credentials"
DEFAULT_PLATFORM_URL = os.environ.get("AI_HUB_URL", "")
DEFAULT_TOKEN = os.environ.get("AI_HUB_TOKEN", "")
SKILL_MD = "SKILL.md"
SCAN_DIRS = [
    Path.home() / ".agents" / "skills",
    Path.home() / ".hermes" / "skills",
    Path.home() / ".claude" / "skills",
]


@dataclass
class ErrorDetail:
    path: str = ""
    field: str | None = None
    reason: str = ""


@dataclass
class SkillPreview:
    path: str
    name: str = ""
    description: str = ""
    file_count: int = 0
    valid: bool = True
    errors: list[ErrorDetail] = field(default_factory=list)


# ── 配置 ──────────────────────────────────────────────

def load_config() -> tuple[str, str]:
    """加载平台 URL 和 PAT。优先级：环境变量 > credentials 文件。"""
    url = DEFAULT_PLATFORM_URL
    token = DEFAULT_TOKEN
    if CREDENTIALS_FILE.exists():
        cp = configparser.ConfigParser()
        cp.read(CREDENTIALS_FILE, encoding="utf-8")
        default = cp["default"] if cp.has_section("default") else {}
        if not url:
            url = default.get("url", "").strip()
        if not token:
            token = default.get("token", "").strip()
    return url, token


def save_token(url: str, token: str) -> None:
    """保存 token 到 ~/.ai-hub/credentials 并设 0600 权限。"""
    CREDENTIALS_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    cp = configparser.ConfigParser()
    if CREDENTIALS_FILE.exists():
        cp.read(CREDENTIALS_FILE, encoding="utf-8")
    if not cp.has_section("default"):
        cp.add_section("default")
    if url:
        cp.set("default", "url", url)
    cp.set("default", "token", token)
    with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
        cp.write(f)
    # 权限收紧：Unix 用 chmod 0600；Windows 上 chmod 仅设只读标志，
    # 需额外依赖 icacls 或 keyring 库实现真正限制，当前仅做最大努力保护。
    try:
        os.chmod(CREDENTIALS_FILE, 0o600)
    except Exception:
        pass  # 非 Unix 平台静默降级


def clear_token() -> None:
    """清除已保存的 token。"""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


# ── API 客户端 ─────────────────────────────────────────

class APIError(Exception):
    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        display = str(detail) if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)
        super().__init__(display)


def publish_skill_api(
    url: str, token: str, slug: str, version: str, zip_bytes: bytes,
    category: str = "general", kind: str = "tool", changelog: str = "",
    author: str = "", tags: str = "",
) -> dict:
    """调 POST /api/v1/skills 发布技能（multipart/form-data）。"""
    boundary = "----skillpublisher" + os.urandom(16).hex()
    body_parts: list[bytes] = []

    def add_field(name: str, value: str) -> None:
        body_parts.append(f"--{boundary}\r\n".encode())
        body_parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body_parts.append(value.encode() + b"\r\n")

    add_field("slug", slug)
    add_field("version", version)
    if changelog:
        add_field("changelog", changelog)
    if author:
        add_field("author", author)
    if kind:
        add_field("kind", kind)
    if category:
        add_field("category", category)
    if tags:
        add_field("tags", tags)

    # 文件字段
    body_parts.append(f"--{boundary}\r\n".encode())
    body_parts.append(b'Content-Disposition: form-data; name="files"; filename="skill.zip"\r\n')
    body_parts.append(b"Content-Type: application/zip\r\n\r\n")
    body_parts.append(zip_bytes + b"\r\n")
    body_parts.append(f"--{boundary}--\r\n".encode())

    import urllib.parse
    body = b"".join(body_parts)
    query_params = urllib.parse.urlencode({"slug": slug, "version": version})
    full_url = url.rstrip("/") + "/api/v1/skills?" + query_params
    req = Request(
        full_url, data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    return _do_request(req)


def search_skills_api(url: str, token: str, query: str) -> list:
    """调 GET /api/v1/skills/search?q=... 查重。"""
    import urllib.parse
    full_url = url.rstrip("/") + "/api/v1/skills/search?q=" + urllib.parse.quote(query)
    req = Request(full_url, headers={"Authorization": f"Bearer {token}"})
    return _do_request(req)  # type: ignore[return-value]


def _do_request(req: Request) -> Any:
    try:
        with urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
            detail = err_body.get("detail", str(e))
        except Exception:
            detail = str(e)
        raise APIError(e.code, detail) from None
    except URLError as e:
        raise APIError(0, f"无法连接平台：{e.reason}，请检查网络和 AI_HUB_URL 配置") from None
    except json.JSONDecodeError:
        raise APIError(0, "无法解析平台响应，请检查 AI_HUB_URL 是否指向正确地址") from None
    except OSError as e:
        raise APIError(0, f"网络请求超时或中断：{e}") from None


# ── 前端校验（纯函数，同 validate_service.py 规则子集）─

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_DESC_LEN = 1024
MAX_NAME_LEN = 64


class ValidationFailed(Exception):
    def __init__(self, message: str, errors: list[ErrorDetail]) -> None:
        self.message = message
        self.errors = errors
        super().__init__(message)


def parse_skill_md(content: str) -> tuple[dict, str]:
    """解析 SKILL.md 的 YAML frontmatter，不依赖平台后端。"""
    errors: list[ErrorDetail] = []
    if not content.startswith("---"):
        errors.append(ErrorDetail(path=SKILL_MD, reason="文件必须以 YAML frontmatter 开头（首行应为 ---）"))
    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append(ErrorDetail(path=SKILL_MD, reason="frontmatter 未闭合（缺少结尾的 ---）"))
    if errors:
        raise ValidationFailed("SKILL.md 格式不正确", errors)

    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        raise ValidationFailed(
            "SKILL.md 格式不正确",
            [ErrorDetail(path=SKILL_MD, reason="frontmatter 的 YAML 格式有误，请检查缩进、冒号、引号等语法")],
        ) from None

    if not isinstance(fm, dict):
        raise ValidationFailed(
            "SKILL.md 格式不正确",
            [ErrorDetail(path=SKILL_MD, reason="frontmatter 必须是一个键值对映射")],
        )
    return fm, parts[2].strip()


def validate_before_publish(content: str, slug: str) -> list[ErrorDetail]:
    """发布前本地预校验，与平台 validate_frontmatter 规则对齐。全部通过返回空列表。"""
    errors: list[ErrorDetail] = []
    try:
        fm, _body = parse_skill_md(content)
    except ValidationFailed as e:
        return e.errors

    name = fm.get("name", "")
    if not name:
        errors.append(ErrorDetail(path=SKILL_MD, field="name", reason="name 为必填项"))
    elif not isinstance(name, str) or not SLUG_RE.match(name) or len(name) > MAX_NAME_LEN:
        errors.append(ErrorDetail(
            path=SKILL_MD, field="name",
            reason="name 必须为 1-64 个字符，只能包含小写字母、数字和连字符（不允许空格、下划线、中文或大写字母）",
        ))
    elif name != slug:
        errors.append(ErrorDetail(
            path=SKILL_MD, field="name",
            reason=f"name（{name}）必须与 slug（{slug}）一致",
        ))

    desc = fm.get("description", "")
    if not desc:
        errors.append(ErrorDetail(path=SKILL_MD, field="description", reason="description 为必填项"))
    elif not isinstance(desc, str) or len(desc) > MAX_DESC_LEN:
        errors.append(ErrorDetail(
            path=SKILL_MD, field="description",
            reason="description 必须为 1-1024 个字符",
        ))

    return errors


# ── 打包 ───────────────────────────────────────────────

SKIP_PATTERNS = {"__pycache__", ".git", ".DS_Store", ".venv", "node_modules"}
SKIP_EXTENSIONS = {".gz", ".zip", ".7z", ".tar", ".rar"}


def pack_skill_dir(skill_dir: Path) -> bytes:
    """将技能目录打成 ZIP 字节。过滤 __pycache__、.git 等。"""
    buf = io.BytesIO()
    base = skill_dir.resolve()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fpath in base.rglob("*"):
            if fpath.is_file() and not any(p in fpath.parts for p in SKIP_PATTERNS):
                if fpath.suffix.lower() in SKIP_EXTENSIONS:
                    continue
                arcname = fpath.relative_to(base).as_posix()
                zf.write(fpath, arcname)
    return buf.getvalue()


def extract_slug_from_path(skill_dir: Path) -> str:
    """从目录路径提取 slug：优先读 SKILL.md 的 name，回退到目录名。"""
    md_path = skill_dir / SKILL_MD
    if md_path.exists():
        try:
            fm, _ = parse_skill_md(md_path.read_text(encoding="utf-8"))
            name = fm.get("name", "")
            if name and SLUG_RE.match(name):
                return name
        except Exception:
            pass
    # 回退：目录名小写、下划线替换
    return skill_dir.name.lower().replace(" ", "-").replace("_", "-")


def format_details(details: list[ErrorDetail | dict]) -> str:
    """将错误明细列表格式化为中文多行文本。接受 dataclass 或 API 返回的 dict。"""
    lines: list[str] = []
    for d in details:
        if isinstance(d, dict):
            field = d.get("field")
            reason = d.get("reason", "")
        else:
            field = d.field
            reason = d.reason
        if field:
            lines.append(f"  • {field}：{reason}")
        else:
            lines.append(f"  • {reason}")
    return "\n".join(lines)
