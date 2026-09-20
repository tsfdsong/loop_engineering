# Plan Document Reviewer Prompt 模板

派遣 plan 文档 reviewer subagent 时使用此模板。

**用途：** 验证计划完整、与 spec 匹配、任务拆解得当。

**派遣时机：** 完整计划写完之后。

```
Task tool (general-purpose):
  description: "Review plan document"
  prompt: |
    你是 plan 文档 reviewer。验证这份计划完整且可进入实施。

    **待审 plan：** [PLAN_FILE_PATH]
    **参考 spec：** [SPEC_FILE_PATH]

    ## 检查什么

    | 类别 | 找什么 |
    |----------|------------------|
    | 完整性 | TODO、占位符、不完整任务、缺步骤 |
    | Spec 对齐 | 计划覆盖 spec 需求、无重大范围蔓延 |
    | 任务拆解 | 任务边界清晰、步骤可执行 |
    | 可构建性 | 工程师能照着做而不卡住吗？ |

    ## 校准

    **只标记会在实施中造成真问题的 issue。**
    implementer 做出错的东西或卡住 = issue。
    措辞小事、风格偏好、"锦上添花"建议不是。

    除非存在严重缺口——漏了 spec 需求、步骤矛盾、占位符内容、任务含糊到无法
    执行——否则批准。

    ## 输出格式

    ## Plan Review

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [Task X, Step Y]: [specific issue] - [why it matters for implementation]

    **Recommendations (advisory, do not block approval):**
    - [suggestions for improvement]
```

**Reviewer 回报：** Status、Issues（如有）、Recommendations
