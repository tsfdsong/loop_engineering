"""
编排层可执行脚本包

模块组成:
- state_manager.py        状态文件管理(线程安全 · 机制④)
- git_ops.py              Git 操作(原子性 · 机制③)
- worker_contract.py      Worker Contract v1 (packet/result)
- worker_adapter.py       Runtime adapter 注册表
- adapters/               cursor / zcode / stub adapters
- task_scheduler.py       DAG 并发调度 (v5.0)
- zcode_runner.py         ZCode CLI + prompt 构建 (降级路径)
- complexity_evaluator.py L0 复杂度评估(纯规则 · 机制①)
- orchestrator.py         主调度器(串联所有模块)
"""
