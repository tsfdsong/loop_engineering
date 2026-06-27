"""
降级兜底管理模块(机制④ · DeepSeek A+C 组合)

配额耗尽时自动切 DeepSeek,执行不打断用户。
- 方案A: ZCode config 切换(保留 ZCode 工具能力)
- 方案C: DeepSeek API 直连(零干扰,编排层自身逻辑用)
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# DeepSeek 配置
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_API_ENDPOINT = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODELS = {
    "main": "deepseek-chat",
    "pro": "deepseek-v4-pro",
    "flash": "deepseek-v4-flash",
}

# ZCode config 路径
ZCODE_CONFIG_PATH = os.path.expanduser("~/.zcode/cli/config.json")
ZCODE_CONFIG_BAK = ZCODE_CONFIG_PATH + ".bak"

# DeepSeek API key(从环境变量读取,不硬编码)
def get_deepseek_api_key():
    """读取 DeepSeek API key(优先环境变量)"""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    # 回退: 尝试从 ZCode db 或其他配置读取(略)
    return None


# ─────────────────────────────────────────────
# 方案A: ZCode config 切换(保留 ZCode 工具能力)
# ─────────────────────────────────────────────

def build_deepseek_config(original_config=None):
    """
    构造 DeepSeek 的 ZCode config(实测验证过的格式)。

    Args:
        original_config: 原 config(保留 plugins/mcp 等非模型字段)
    """
    api_key = get_deepseek_api_key()
    config = original_config or {}
    # 注入 DeepSeek provider
    config["provider"] = {
        "deepseek": {
            "kind": "openai-compatible",
            "options": {
                "baseURL": DEEPSEEK_BASE_URL,
                "apiKey": api_key,
            },
        }
    }
    # model.main 用字符串格式(实测有效)
    config["model"] = {"main": "deepseek/deepseek-chat"}
    return config


def switch_to_deepseek_config():
    """
    方案A: 备份 config → 写入 DeepSeek config。

    Returns:
        bool: 切换是否成功
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        print("⚠️ 未找到 DEEPSEEK_API_KEY 环境变量,无法降级", file=sys.stderr)
        return False

    # 备份原 config
    if os.path.exists(ZCODE_CONFIG_PATH):
        shutil.copy2(ZCODE_CONFIG_PATH, ZCODE_CONFIG_BAK)

    # 读取原 config(保留 plugins/mcp 等)
    original = {}
    if os.path.exists(ZCODE_CONFIG_BAK):
        try:
            with open(ZCODE_CONFIG_BAK, "r", encoding="utf-8") as f:
                original = json.load(f)
        except (json.JSONDecodeError, OSError):
            original = {}

    # 构造 DeepSeek config
    config = build_deepseek_config(original)

    # 原子写入
    tmp = ZCODE_CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ZCODE_CONFIG_PATH)

    print(f"✅ 已切换 ZCode config 到 DeepSeek(方案A)")
    return True


def restore_config():
    """方案A: 恢复原 config(任务完成后立即调用)"""
    if os.path.exists(ZCODE_CONFIG_BAK):
        shutil.copy2(ZCODE_CONFIG_BAK, ZCODE_CONFIG_PATH)
        os.unlink(ZCODE_CONFIG_BAK)
        print("✅ 已恢复原 ZCode config")
        return True
    return False


# ─────────────────────────────────────────────
# 方案C: DeepSeek API 直连(零干扰)
# ─────────────────────────────────────────────

def call_deepseek_api(prompt, model=None, max_tokens=2000, timeout=120):
    """
    方案C: 直接调 DeepSeek API(编排层自身逻辑用,零干扰)。

    适用场景: 编排层需要 LLM 做摘要/判断,不想干扰任何工具会话。

    Returns:
        dict: {success, content, error}
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        return {"success": False, "content": None, "error": "缺少 DEEPSEEK_API_KEY"}

    payload = {
        "model": model or DEEPSEEK_MODELS["main"],
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        result = subprocess.run(
            [
                "curl", "-s", "--max-time", str(timeout),
                DEEPSEEK_API_ENDPOINT,
                "-H", f"Authorization: Bearer {api_key}",
                "-H", "content-type: application/json",
                "-d", json.dumps(payload),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        data = json.loads(result.stdout)
        if "error" in data:
            return {"success": False, "content": None, "error": data["error"]}
        content = data["choices"][0]["message"]["content"]
        return {"success": True, "content": content, "error": None}
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return {"success": False, "content": None, "error": str(e)}
    except subprocess.TimeoutExpired:
        return {"success": False, "content": None, "error": "DeepSeek API 超时"}


# ─────────────────────────────────────────────
# 降级执行子任务(方案A 完整流程)
# ─────────────────────────────────────────────

def execute_with_degradation(project_dir, task, prompt, mode="yolo"):
    """
    降级执行: config 切 DeepSeek → ZCode 执行 → 恢复 config。

    透明化标记由调用方(zcode_runner)写入状态文件。
    """
    # 1. 切换 config 到 DeepSeek
    if not switch_to_deepseek_config():
        return {"status": "failed", "error": "降级 config 切换失败"}

    try:
        # 2. 用 DeepSeek config 调用 ZCode(保留工具能力)
        from zcode_runner import call_zcode, ZCODE_CLI_PATH
        # 设置 DEEPSEEK_API_KEY 环境变量供 ZCode 读取
        env = os.environ.copy()
        env["DEEPSEEK_API_KEY"] = get_deepseek_api_key()

        import subprocess as sp
        cmd = [
            "node", ZCODE_CLI_PATH,
            "--prompt", prompt,
            "--cwd", str(project_dir),
            "--mode", mode,
        ]
        result = sp.run(cmd, cwd=str(project_dir), capture_output=True,
                        text=True, encoding="utf-8", env=env, timeout=600)

        success = result.returncode == 0
        return {
            "status": "completed" if success else "failed",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "actual_model": "deepseek-chat",
        }
    finally:
        # 3. 无论成功失败,都恢复原 config(关键!)
        restore_config()
