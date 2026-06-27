"""
L0 复杂度评估模块(机制① · 纯规则,零 token)

不调 LLM,纯关键词+信号匹配判断任务走 L1/L2/L3 哪一档。
误差靠硬闸门+门禁验收纠正。
"""
import re

# L1 直通档关键词
L1_KEYWORDS = [
    "typo", "错别字", "改字符串", "加注释", "改文案", "修拼写",
    "改常量", "改配置值", "改提示语", "改变量名", "修缩进", "改格式",
]

# L2 标准档关键词
L2_KEYWORDS = [
    "新增api", "写测试", "单元测试", "重构函数", "优化查询", "加字段",
    "单功能", "接口", "端点", "服务", "中间件", "钩子", "工具函数",
    "修bug", "修复", "添加", "实现",
]

# L3 完整档关键词
L3_KEYWORDS = [
    "跨模块", "架构", "重构", "新系统", "重写", "迁移", "改造",
    "集成", "联调", "新功能", "平台", "框架", "全栈", "端到端",
    "系统", "模块", "整体",
]

# 跨工具信号(同时涉及前后端)
FRONTEND_SIGNALS = ["前端", "页面", "ui", "组件", "css", "动画", "界面"]
BACKEND_SIGNALS = ["后端", "api", "数据库", "接口", "服务端"]
REVIEW_SIGNALS = ["审查", "review", "架构设计", "审计"]


def estimate_file_count(feature_desc):
    """
    从功能描述预估影响文件数(启发式)。

    Returns:
        int: 预估文件数
    """
    desc_lower = feature_desc.lower()
    count = 0
    # 每个模块关键词 +1
    module_signals = ["表", "model", "api", "页面", "组件", "测试", "路由", "服务"]
    for sig in module_signals:
        if sig in desc_lower:
            count += 1
    return max(count, 1)


def is_cross_tool(feature_desc):
    """判断是否跨工具(同时涉及前端+后端+审查)"""
    desc_lower = feature_desc.lower()
    has_frontend = any(s in desc_lower for s in FRONTEND_SIGNALS)
    has_backend = any(s in desc_lower for s in BACKEND_SIGNALS)
    has_review = any(s in desc_lower for s in REVIEW_SIGNALS)
    # 前端+后端,或涉及审查的复杂任务
    return (has_frontend and has_backend) or (has_frontend and has_review)


def match_keywords(text, keywords):
    """检查文本是否命中任一关键词(返回命中的关键词列表)"""
    text_lower = text.lower()
    return [kw for kw in keywords if kw in text_lower]


def evaluate_complexity(feature_desc, explicit_flag=None):
    """
    L0 复杂度评估(纯规则,零 token)。

    Args:
        feature_desc: 功能描述
        explicit_flag: 用户显式指定('fast'/'full'/None)

    Returns:
        dict: {
            tier: 'L1'/'L2'/'L3',
            reason: 评估理由,
            signals: 命中的信号详情
        }
    """
    signals = {}

    # Step 1: 显式指定优先
    if explicit_flag == "fast":
        return {
            "tier": "L1",
            "reason": "用户显式指定 -fast",
            "signals": {"explicit": "fast"},
        }
    if explicit_flag == "full":
        return {
            "tier": "L3",
            "reason": "用户显式指定 -full",
            "signals": {"explicit": "full"},
        }

    # 收集信号
    file_count = estimate_file_count(feature_desc)
    cross_tool = is_cross_tool(feature_desc)
    l1_hits = match_keywords(feature_desc, L1_KEYWORDS)
    l2_hits = match_keywords(feature_desc, L2_KEYWORDS)
    l3_hits = match_keywords(feature_desc, L3_KEYWORDS)

    signals = {
        "file_count": file_count,
        "cross_tool": cross_tool,
        "l1_keywords": l1_hits,
        "l2_keywords": l2_hits,
        "l3_keywords": l3_hits,
    }

    # Step 2: L1 关键词强匹配 + 文件数=1
    if l1_hits and file_count == 1:
        return {
            "tier": "L1",
            "reason": f"L1关键词命中({l1_hits})且文件数=1",
            "signals": signals,
        }

    # Step 3: 跨工具判定 → L3
    if cross_tool:
        return {
            "tier": "L3",
            "reason": "跨工具任务(涉及前端+后端/审查)",
            "signals": signals,
        }

    # Step 4: 文件数判定
    if file_count > 5:
        return {
            "tier": "L3",
            "reason": f"影响文件数 {file_count} >5",
            "signals": signals,
        }
    if file_count >= 2:
        return {
            "tier": "L2",
            "reason": f"影响文件数 {file_count} 在 2-5 范围",
            "signals": signals,
        }

    # Step 5: 关键词判定
    if l3_hits:
        return {
            "tier": "L3",
            "reason": f"L3关键词命中({l3_hits})",
            "signals": signals,
        }
    if l2_hits:
        return {
            "tier": "L2",
            "reason": f"L2关键词命中({l2_hits})",
            "signals": signals,
        }

    # Step 6: 默认兜底 → L2(让硬闸门纠正)
    return {
        "tier": "L2",
        "reason": "无法明确判断,默认 L2 标准档(硬闸门可调整)",
        "signals": signals,
    }
