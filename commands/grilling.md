---
description: 显式触发 grilling——对已有方案 / spec 做穷尽式审讯
---

调用 Skill 工具加载 **grilling** 技能，对用户指定的方案 / 计划 / 设计 / spec（未指定则追问目标文件）执行穷尽式审讯：

- frontier 决策树 + AskUserQuestion 轮次（每轮 ≤ 4 题）
- 事实派 sub-agent 查，决策交用户
- frontier 清空 + 用户确认共识后终止；审讯修订写回原 spec 文件

不传参时先确认审讯对象（spec 文件路径或方案描述），不要猜。
