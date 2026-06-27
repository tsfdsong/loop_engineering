"""
编排层可执行脚本包

模块组成:
- state_manager.py      状态文件管理(双轨制 · 机制④)
- git_ops.py            Git 操作(原子性 · 机制③)
- zcode_runner.py       ZCode CLI 调用(调度执行)
- complexity_evaluator.py  L0 复杂度评估(纯规则 · 机制①)
- degradation_manager.py   DeepSeek 降级兜底(机制④)
- cursor_collaboration.py  Cursor 半自动协作(机制⑤)
- orchestrator.py       主调度器(串联所有模块)
"""
