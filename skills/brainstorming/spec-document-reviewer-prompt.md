# Spec Document Reviewer Prompt 模板

派遣 spec 文档 reviewer subagent 时使用此模板。

**用途：** 验证 spec 完整、一致、可进入实施计划。

**派遣时机：** spec 文档写入 docs/superpowers/specs/ 之后

```
Task tool (general-purpose):
  description: "Review spec document"
  prompt: |
    你是 spec 文档 reviewer。验证这份 spec 完整且可进入计划阶段。

    **待审 spec：** [SPEC_FILE_PATH]

    ## 检查什么

    | 类别 | 找什么 |
    |----------|------------------|
    | 完整性 | TODO、占位符、"TBD"、未完成小节 |
    | 一致性 | 内部矛盾、冲突的需求 |
    | 清晰度 | 歧义大到可能导致别人做出错的东西 |
    | 范围 | 聚焦到单个计划装得下——不是覆盖多个独立子系统 |
    | YAGNI | 未被要求的功能、过度设计 |
    | **Loop Execution Contract** | Goal + Acceptance Contract（可观察 pass/fail）+ Non-goals + Stop Escalation 齐全；无 G0–G9 / self-healing 复制粘贴 |

    ## 校准

    **只标记会在实施计划阶段造成真问题的 issue。**
    缺失小节、矛盾、或歧义到可被解读成两种意思的需求——这些是 issue。
    措辞小改进、风格偏好、"某节没别的节详细"不是。

    除非存在会导致坏计划的严重缺口，否则批准。

    ## 输出格式

    ## Spec Review

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [Section X]: [specific issue] - [why it matters for planning]

    **Recommendations (advisory, do not block approval):**
    - [suggestions for improvement]
```

**Reviewer 回报：** Status、Issues（如有）、Recommendations
