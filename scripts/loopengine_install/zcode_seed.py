"""ZCode plugin seed hash helper (extracted from legacy install_zcode_plugin)."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path

SEED_ALLOW = frozenset(
    {
        ".mcp.json",
        ".zcode-plugin",
        "README.md",
        "commands",
        "dist",
        "hooks",
        "output-styles",
        "package.json",
        "skills",
        "templates",
    }
)
SEED_SKIP_DIRS = frozenset({"node_modules", ".turbo", "coverage"})


def compute_seed_hash(plugin_dir: Path) -> tuple[str, str]:
    """Return (hash, status) where status is ``exact`` or ``placeholder``."""
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
                capture_output=True,
                text=True,
                check=True,
                timeout=15,
            )
            return out.stdout.strip(), "exact"
        except Exception:
            pass
    digest = hashlib.sha256()
    for p in sorted(plugin_dir.rglob("*")):
        if p.is_file() and ".zcode-plugin-seed.json" not in str(p):
            digest.update(str(p.relative_to(plugin_dir)).encode())
            digest.update(p.read_bytes())
    return digest.hexdigest(), "placeholder"
