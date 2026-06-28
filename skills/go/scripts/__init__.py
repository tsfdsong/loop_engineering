"""
编排层可执行脚本包

模块组成:
- state_manager.py      状态文件管理(线程安全 · 机制④)
- git_ops.py            Git 操作(原子性 · 机制③)
- zcode_runner.py       ZCode CLI 调用(多进程并发)
- complexity_evaluator.py  L0 复杂度评估(纯规则 · 机制①)
- orchestrator.py       主调度器(串联所有模块)
"""
