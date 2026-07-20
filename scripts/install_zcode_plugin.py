#!/usr/bin/env python3
# ════════════════════════════════════════════════════════════
# install_zcode_plugin.py — DEPRECATED CLI（emergency / hash helper）
# ════════════════════════════════════════════════════════════
#
# DEPRECATED: production install is `python3 install.py install` via
# loopengine_install.adapters.zcode. Prefer that path.
#
# Still used as a library: adapters import compute_seed_hash().
# CLI below is emergency fallback only (debug / offline recovery).
#
# 根因验证（zcode.cjs 逆向，2026-07-14）：
#   - 插件发现路径 scanOfficialCache + loadPlugin 只看：目录存在 +
#     .zcode-plugin/plugin.json 的 name 合法 + marketplace.json 列表。
#   - seed.json 的 hash 在加载时【不校验】（verifyHash=0）。
#
# 用法（emergency）：
#   python3 scripts/install_zcode_plugin.py              # 安装/升级
#   python3 scripts/install_zcode_plugin.py --uninstall  # 卸载（删三件套）
#   python3 scripts/install_zcode_plugin.py --dry-run    # 只打印计划不写盘
#
# 依赖：纯标准库；可选 node（compute_seed_hash；不可用则占位 hash）。
#
# 与 install.sh 的关系：互补不冲突。install.sh 管 skills filesystem 部署 +
# 红线注入 + MCP；本脚本额外补「插件管理可见」三件套。
# ════════════════════════════════════════════════════════════

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# 单一真源（红线 9 R5.2 减法）：从 render_plugins / _lib 导入，删除本文件内嵌的
# deep_merge / strip_meta 重复实现。注释中曾经承诺的"复用 render_plugins.py 的
# 合并逻辑"现在真正落地（消除 v6.x 注释/代码不一致的诚信问题）。
from _lib.json_io import deep_merge, strip_meta, write_json

# ── 常量 ──────────────────────────────────────────────────
PLUGIN_NAME = "loopengine"
MARKETPLACE_ID = "zcode-plugins-official"
# 版本号：与 .plugin-template.json 的 version 保持一致（目录==manifest version 自洽，
# 与 zcode-guide 的 0.1.0==0.1.0 模式一致）。如需改版本，同步改 .plugin-template.json。
# 从模板读取，避免硬编码漂移。
WHITELIST_TOP_LEVEL = {
    ".mcp.json", ".zcode-plugin", "README.md", "commands", "dist",
    "hooks", "output-styles", "package.json", "skills", "templates",
}

# ZCode 路径（macOS/Linux 通用，~ 展开）
ZCODE_HOME = Path.home() / ".zcode"
CACHE_ROOT = ZCODE_HOME / "cli" / "plugins" / "cache" / MARKETPLACE_ID
MARKETPLACE_JSON = ZCODE_HOME / "cli" / "plugins" / "marketplaces" / MARKETPLACE_ID / "marketplace.json"
CONFIG_JSON = ZCODE_HOME / "cli" / "config.json"
ENABLE_SCRIPT = "register_zcode_plugin.py"  # 仓库内既有脚本，幂等写 enabledPlugins

# seed hash 白名单（与 zcode.cjs 逆向一致：仅这些顶层目录/文件进入 hash）
SEED_ALLOW = WHITELIST_TOP_LEVEL
SEED_SKIP_DIRS = {"node_modules", ".turbo", "coverage"}


# ── 工具函数 ──────────────────────────────────────────────
def find_repo_root() -> Path:
    """从 git 定位仓库根（不依赖 cwd）。失败则用本文件所在目录上溯。"""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        root = Path(out.stdout.strip())
        if (root / ".plugin-template.json").exists():
            return root
    except Exception:
        pass
    # fallback：本文件在 scripts/ 下，根是上一级
    here = Path(__file__).resolve().parent
    return here.parent


def read_template_version(repo_root: Path) -> str:
    """从 .plugin-template.json 读 version（单一真源，避免硬编码漂移）。"""
    tmpl = repo_root / ".plugin-template.json"
    with open(tmpl, encoding="utf-8") as f:
        return json.load(f)["version"]


def render_zcode_manifest(repo_root: Path) -> dict:
    """复用 _lib.json_io 的合并逻辑产出 ZCode plugin.json（深合并 template+overlay，
    去元字段，去 mcpServers）。deep_merge / strip_meta 从 _lib.json_io 单一真源导入。"""
    template = json.loads((repo_root / ".plugin-template.json").read_text(encoding="utf-8"))
    overlay = json.loads((repo_root / ".zcode-plugin" / "plugin.json").read_text(encoding="utf-8"))
    merged = strip_meta(deep_merge(strip_meta(template), overlay))
    # ZCode adapter drop_fields = ["mcpServers"]（MCP 写 config.json，不进 plugin.json）
    merged.pop("mcpServers", None)
    return merged


def compute_seed_hash(plugin_dir: Path) -> tuple[str, str]:
    """计算 seed hash（近似 zcode.cjs 算法）。返回 (hash, status)。
    status='exact' 若 node 可用并成功；'placeholder' 若 node 不可用（回退确定性占位）。

    注意：hash 在加载时不被校验（已逆向验证），故近似/占位均不影响插件加载。
    本实现尽力复现官方算法，但未与官方 bit-for-bit 对齐（官方内部 stringify 细节未公开）。
    """
    node = shutil.which("node")
    if node:
        try:
            script = r'''
const fs=require("fs"),path=require("path"),crypto=require("crypto");
const dir=process.argv[1];
const allow=new Set([".mcp.json",".zcode-plugin","README.md","commands","dist","hooks","output-styles","package.json","skills","templates"]);
const skipDir=new Set(["node_modules",".turbo","coverage"]);
let arr=[];
(function walk(base,rel){
  for(const e of fs.readdirSync(base,{withFileTypes:true})){
    const r=rel?rel+"/"+e.name:e.name;
    if(rel===""){ if(!allow.has(e.name)) continue; }
    if(e.isDirectory()){ if(skipDir.has(e.name)) continue; walk(path.join(base,e.name),r); }
    else {
      if(e.name===".zcode-plugin-seed.json") continue;
      const buf=fs.readFileSync(path.join(base,e.name));
      const sha=crypto.createHash("sha256").update(buf).digest("hex");
      const st=fs.statSync(path.join(base,e.name)).mode;
      const mode=((st&73)!==0)||/dist\/mcp\/server\.js$/.test(r)||(/^hooks\//.test(r)&&!/\.(json|md|txt)$/.test(r))?493:420;
      arr.push([r,sha,mode]);
    }
  }
})(dir,"");
arr.sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0);
process.stdout.write(crypto.createHash("sha256").update(Buffer.from(JSON.stringify(arr))).digest("hex"));
'''
            out = subprocess.run(
                [node, "-e", script, "--", str(plugin_dir)],
                capture_output=True, text=True, check=True, timeout=15,
            )
            return out.stdout.strip(), "exact"
        except Exception as e:
            print(f"  ⚠️  node hash 计算失败（{e}），回退占位 hash", file=sys.stderr)
    # 占位：对目录树取确定性 sha256（加载时不校验，仅作标记）
    h = hashlib.sha256()
    for p in sorted(plugin_dir.rglob("*")):
        if p.is_file() and ".zcode-plugin-seed.json" not in str(p):
            h.update(str(p.relative_to(plugin_dir)).encode())
            h.update(p.read_bytes())
    return h.hexdigest(), "placeholder"


def copy_payload(repo_root: Path, dest: Path) -> int:
    """从仓库复制白名单顶层目录/文件到 dest。返回复制的条目数。
    幂等：先清 dest 内旧内容再复制（仅清 dest 自身，不动外部）。"""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    count = 0
    for name in sorted(os.listdir(repo_root)):
        if name not in WHITELIST_TOP_LEVEL:
            continue
        src = repo_root / name
        dst = dest / name
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=False)
        else:
            shutil.copy2(src, dst)
        count += 1
    return count


def write_manifest(dest: Path, manifest: dict) -> None:
    """写 .zcode-plugin/plugin.json（与 render_plugins.py 输出格式一致）。"""
    pdir = dest / ".zcode-plugin"
    pdir.mkdir(exist_ok=True)
    write_json(pdir / "plugin.json", manifest)


def write_seed(dest: Path, version: str, hash_val: str) -> None:
    """写 .zcode-plugin-seed.json（7 字段，与官方格式一致）。"""
    seed = {
        "hash": hash_val,
        "marketplace": MARKETPLACE_ID,
        "plugin": PLUGIN_NAME,
        "pluginVersion": version,
        "source": "filesystem",
        "version": 1,
    }
    write_json(dest / ".zcode-plugin-seed.json", seed)


def update_marketplace(version: str, dry_run: bool) -> bool:
    """幂等追加/更新 marketplace.json 的 loopengine 条目。返回是否改动。"""
    if not MARKETPLACE_JSON.exists():
        print(f"  ❌ marketplace.json 不存在: {MARKETPLACE_JSON}", file=sys.stderr)
        return False
    mp = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    cache_path = str(CACHE_ROOT / PLUGIN_NAME / version)
    entry = {
        "cachePath": cache_path,
        "name": PLUGIN_NAME,
        "source": "filesystem",
        "version": version,
    }
    plugins = mp.setdefault("plugins", [])
    # 查找已有 loopengine 条目（按 name 匹配）
    existing = next((p for p in plugins if p.get("name") == PLUGIN_NAME), None)
    changed = False
    if existing is None:
        plugins.append(entry)
        changed = True
    elif (existing.get("cachePath") != cache_path
          or existing.get("version") != version):
        existing.update(entry)
        changed = True
    if changed and not dry_run:
        # 备份后原子写
        bak = MARKETPLACE_JSON.with_suffix(".json.bak")
        shutil.copy2(MARKETPLACE_JSON, bak)
        write_json(MARKETPLACE_JSON, mp)
    return changed


def ensure_enabled(repo_root: Path, dry_run: bool) -> bool:
    """调既有 register_zcode_plugin.py 幂等写 config.json::enabledPlugins。"""
    reg = repo_root / "scripts" / ENABLE_SCRIPT
    if not reg.exists():
        print(f"  ⚠️  {ENABLE_SCRIPT} 不存在，跳过 enabledPlugins（请确认 config.json 手动设置）", file=sys.stderr)
        return False
    if dry_run:
        print(f"  [dry-run] 将调用 {ENABLE_SCRIPT}")
        return True
    try:
        subprocess.run(
            [sys.executable, str(reg), str(CONFIG_JSON), PLUGIN_NAME, MARKETPLACE_ID],
            check=True, capture_output=True, text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  {ENABLE_SCRIPT} 失败: {e.stderr or e.stdout}", file=sys.stderr)
        return False


# ── 主流程 ────────────────────────────────────────────────
def cmd_install(repo_root: Path, dry_run: bool) -> int:
    version = read_template_version(repo_root)
    plugin_dir = CACHE_ROOT / PLUGIN_NAME / version
    print(f"📦 安装 {PLUGIN_NAME}@{version} 为 ZCode 插件")
    print(f"   cache dir : {plugin_dir}")
    print(f"   marketplace: {MARKETPLACE_JSON}")

    # 1. 渲染 manifest
    manifest = render_zcode_manifest(repo_root)
    if manifest.get("name") != PLUGIN_NAME:
        print(f"  ❌ manifest name 不是 {PLUGIN_NAME}: {manifest.get('name')}", file=sys.stderr)
        return 1

    # 2. dry-run 早输出计划
    if dry_run:
        print("\n  [dry-run] 计划：")
        print(f"    1. 复制 payload（白名单顶层）→ {plugin_dir}")
        print(f"    2. 写 .zcode-plugin/plugin.json (name={PLUGIN_NAME}, version={version})")
        print(f"    3. 写 .zcode-plugin-seed.json (marketplace={MARKETPLACE_ID})")
        print(f"    4. 追加 marketplace.json 条目 (version={version})")
        print(f"    5. 调 {ENABLE_SCRIPT} 确保 enabledPlugins")
        return 0

    # 3. 复制 payload
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    n = copy_payload(repo_root, plugin_dir)
    print(f"  ✅ 复制 {n} 个白名单顶层条目 → {plugin_dir}")

    # 4. 写 manifest
    write_manifest(plugin_dir, manifest)
    print(f"  ✅ 写 .zcode-plugin/plugin.json")

    # 5. 算 hash + 写 seed
    hash_val, status = compute_seed_hash(plugin_dir)
    write_seed(plugin_dir, version, hash_val)
    note = "" if status == "exact" else "（近似/占位，加载时不校验）"
    print(f"  ✅ 写 .zcode-plugin-seed.json [{status}]{note}")

    # 6. 更新 marketplace.json
    if update_marketplace(version, dry_run):
        print(f"  ✅ 更新 marketplace.json（loopengine@{version}）")
    else:
        print(f"  ℹ️  marketplace.json 已是最新（无需改动）")

    # 7. 确保 enabledPlugins
    if ensure_enabled(repo_root, dry_run):
        print(f"  ✅ 确保 enabledPlugins: loopengine@{MARKETPLACE_ID}=true")

    print(f"\n✅ 安装完成。重启 ZCode 会话后，插件管理应显示 loopengine。")
    return 0


def cmd_uninstall(version_override: str | None, dry_run: bool) -> int:
    """卸载：删 cache 版本目录 + marketplace 条目。不删 enabledPlugins（留给用户）。"""
    # 找已装的版本目录
    plugin_base = CACHE_ROOT / PLUGIN_NAME
    versions = []
    if plugin_base.exists():
        versions = [d.name for d in plugin_base.iterdir() if d.is_dir()]
    if not versions:
        print(f"ℹ️  未发现已装的 {PLUGIN_NAME}（{plugin_base} 不存在或为空）")
        # 仍尝试清 marketplace 条目
    target_versions = [version_override] if version_override else versions
    print(f"🗑️  卸载 {PLUGIN_NAME}（版本: {target_versions or '无'}）")

    if dry_run:
        for v in target_versions:
            print(f"  [dry-run] 将删 {plugin_base / v}")
        print(f"  [dry-run] 将从 marketplace.json 移除 loopengine 条目")
        return 0

    for v in target_versions:
        d = plugin_base / v
        if d.exists():
            shutil.rmtree(d)
            print(f"  ✅ 删 {d}")
    # 若版本目录清空，删父目录
    if plugin_base.exists() and not any(plugin_base.iterdir()):
        plugin_base.rmdir()
        print(f"  ✅ 删空目录 {plugin_base}")

    # 移除 marketplace 条目
    if MARKETPLACE_JSON.exists():
        mp = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
        before = len(mp.get("plugins", []))
        mp["plugins"] = [p for p in mp.get("plugins", []) if p.get("name") != PLUGIN_NAME]
        after = len(mp["plugins"])
        if before != after:
            bak = MARKETPLACE_JSON.with_suffix(".json.bak")
            shutil.copy2(MARKETPLACE_JSON, bak)
            write_json(MARKETPLACE_JSON, mp)
            print(f"  ✅ 从 marketplace.json 移除 loopengine 条目")

    print(f"\nℹ️  enabledPlugins 未改动（如需禁用，手动改 config.json 或用插件管理 UI）。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=f"把 {PLUGIN_NAME} 注册为正经 ZCode 插件（插件管理可见）"
    )
    ap.add_argument("--uninstall", action="store_true", help="卸载（删三件套）")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划不写盘")
    ap.add_argument("--version", help="指定版本（默认从 .plugin-template.json 读）")
    args = ap.parse_args()

    repo_root = find_repo_root()
    if not (repo_root / ".plugin-template.json").exists():
        print(f"❌ 未找到仓库根（缺 .plugin-template.json）: {repo_root}", file=sys.stderr)
        return 2

    if args.uninstall:
        return cmd_uninstall(args.version, args.dry_run)
    return cmd_install(repo_root, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
