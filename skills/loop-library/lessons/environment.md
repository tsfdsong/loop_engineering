---
id: ENV-001
domain: environment
severity: high
applies_when:
  - task_type: backend
  - task_type: fullstack
  - has_database: true
source: loop/mcp-plaza-0626
created: 2026-06-26
---

## 后端依赖远程服务时优先用 docker-compose 起本地依赖做集成验证

**问题**: loop/mcp-plaza-0626 中，后端依赖远程 PostgreSQL（生产/测试环境 DB），任务执行期间远程 DB 拒绝连接。此时直接放弃集成验证，仅跑单元测试，导致功能完成度审查失效。

**根因**: 未建立"本地依赖回退"机制。远程服务不可达时，没有自动尝试用项目的 docker-compose.yml 起一个本地 DB/Redis，导致 G1（依赖可达）无法通过。

**规则**:
- G1 探测到远程 DB/Redis 不通时，**第一步是检查项目是否有 docker-compose.yml**
- 有 → `docker-compose up -d <db服务名>` 起本地依赖 → 配置环境变量指向本地 → 重新探测
- 起 Docker 失败 → 检查 Docker daemon 是否运行、端口是否冲突 → 修复后重试
- 都失败 → 进入阻塞保护，**明确告知用户**"需要可用的 DB/Redis，请启动本地服务或提供连接方式"，**禁止继续声称验证通过**
- 优先使用本地依赖做集成验证，避免依赖远程环境的不稳定性

**关联门禁**: G1, G8
