# 超级 AI 真人短剧 SKILL 设计方案（v5 · 通用技能版）

> 版本：v5 · 2026-08-31 定稿
> 目标：高效、省成本、追求一定效果 · 根治 AI 真人短剧痛点 · 补齐执行层 MCP 与技能

---

## 〇、定位声明

**drama-studio 是一个通用、可复用、项目无关的超级技能**：

- 安装位置：`~/.zcode/skills/drama-studio/`（全局，跨项目可用；需版本管理时再迁 git 仓库+软链）
- 新项目从零开始：`drama-studio init <项目名>` 生成目录脚手架（见第三节），day-one 即本地目录真源
- 流水线题材无关：P1 真人短剧主线 · P2 漫剧 · P3 预告混剪
- 飞书 Bitable = 可选镜像插件（团队共享/手机查看时再挂），非依赖
- 实测载体：P2 用一个全新项目的首集做全流程实测

---

## 〇.1 资源约束与前提条件（设计依据）

| 类别 | 可用资源 | 边界/限制 | 对方案的影响 |
|------|---------|----------|-------------|
| **文本模型** | MiniMax M3 · DeepSeek V4 | 仅此两款 | 剧本/台词/分镜等文本生成环节的 API 调用只走这两款；管线脚本不依赖其他 LLM |
| **视频/生图模型** | 火山引擎账号已充值：Seedance 2.0 / 2.5 可用 | 按量计费（方舟独立于即梦会员） | 图生视频 API 化（P1）的账号与计费前提已具备；生图可用方舟 doubao-seedream 系 |
| **TTS** | 火山引擎豆包 TTS 模型（随充值账号开通） | 按字符计费（2.8 元/万字符 [T1]） | 豆包 TTS MCP（P1）前提已具备 |
| **即梦** | 基础会员（1080 积分/月） | 即梦 CLI 不可用；网页操作 | 生图/图生视频走即梦网页（人工或 CUA） |
| **可灵** | 少量使用 | 非会员按量 | 官方 MCP 纳入 P2 备选（Seedance 质感不达标时触发），不作主力 |
| 硬件 | M3 Max / 36GB 统一内存 | 视频生成慢 | 本地只跑 whisper/轻量任务，生成全走云端 API |

**设计推论**：火山方舟 = 自动化主通道（视频+TTS+生图一站式）；即梦会员 = 人工精修与积分内产出；可灵 = 质感补丁；MiniMax M3/DeepSeek V4 = 文本管线。**投产主力路线 = 方舟底模 API + 自有 skill 编排**（0.28 元/秒档 [T1]）。

---

## 一、调研结论：最佳实践地图

| 项目 | 热度 | 核心设计（吸收什么） |
|------|------|---------------------|
| **OpenMontage** | 54.8k 星 / 6.8k fork [F 2026-08-31 核验] | ① "把 AI 编程助手变成视频制作工作室"；② 四层执行哲学：**先选流水线→读 manifest→读阶段 skill→调工具**；③ 状态机制片（每步达标才进下一步）；④ 模型无关适配层（README 称 60+ 供应商集成）；⑤ 评分选型引擎；⑥ 规模：README 100+ 工具/700+ skill/12 流水线，第三方教程 52/500（两说并注）；⑦ 安装形态 = git clone 整仓库 + make setup（Python3.10+/FFmpeg/Node18+/Remotion npm），**AGPLv3**；$0.15/条 [T3 单一来源] |
| **LocalMiniDrama**（xuanyustudio） | 真实性已核 [F 2026-08-31] | Seedance 2 接入（走火山方舟 API）+ **真人剧/漫剧双模式**；纯 JS 前端开箱即用（GitHub / 83zi.com）；素材不上云；文字/生图/视频三段 API 自配；成熟度靠 P0 试用 |
| **ViMax**（港大 HKUDS） | 学术出品 | Director/Screenwriter/Producer/Generator 剧组角色分工；叙事规划→视觉一致性→生图→视频→合成全链；默认 Veo/Gemini，换国内 API 有适配成本 [H] |
| DramaClaw | 3.7-4.5k 星 [T2/T3] | script-to-film 通用管线，Docker 自托管；短剧垂直度低 |
| video-use | 12k 星 | "素材文件夹+自然语言"剪辑：口癖/调色/字幕烧录/音频优化 [T3] |
| Voicebox | 33.3k 星 [T3] | 本地语音工作站（克隆+TTS+Agent 语音输出），自带 MCP |
| ElevenLabs 官方 MCP | — | TTS+克隆+音效三合一；SFX v2：48kHz/无缝循环/4 变体 [T1/T2]；海外网络+计费 |
| short-drama-skills（LuxReal） | — | skill 形态：剧本→结构化镜头序列→电影级视频提示词 [T2 GitHub] |
| 一致性工业方案 | — | 固定特征库 + IP-Adapter + LoRA + ControlNet 双保险 [T2] |
| 口型方案 | — | 弃 Wav2Lip → Seedance 2.0 四模态音频输入原生音画同步 [T1 火山文档/T2] |
| **可灵官方 MCP** | 官方出品 [T2] | 批量生成真实角色表演 + 多版本择优；质感上限补丁（P2 备选） |

---

## 二、AI 真人短剧 5 大痛点 → 根治方案映射

| 痛点 | 根治方案 | 落点 |
|------|---------|------|
| 角色一致性 | 角色特征库（定稿图+色盘）+ 参考图机制 + 全能参考白名单 | L2 生图阶段 + L4 知识 |
| 表情呆板 | 分层混合五层法（首帧主力 95%）+ 首帧表情预处理门 | L2 视频阶段质检门 |
| 口型不齐 | **双路线分层**：白名单关键镜用 Seedance 2.0 音频模态（原生音画同步，贵）；量产镜维持视频 2.0 + 后期 TTS（便宜） | L3 MCP 参数 + 流水线规则 |
| 镜间断裂 | BGM 铺底+黑场+空镜内建为剪辑默认动作 | L2 剪辑阶段 |
| 成本失控 | 3 抽纪律 + 试产推算 + 快慢结合（便宜档 95%+贵档白名单 3-5 镜）+ **manifest 成本熔断（默认 100 元/集）** | L1 流水线规则 |

---

## 三、总体架构（四层）

**命名**：`drama-studio`（全局技能）

```
L1 流水线层：drama-studio 按评分选型选流水线（维度 P0 实测后定义，首列"通用可复用性"）
   P1 真人短剧主线 · P2 漫剧 · P3 预告混剪
   manifest = 阶段清单 + 达标条件 + 成本预算（超限熔断，默认 100 元/集）
L2 阶段层（状态机质检门，不过不下传）：
   剧本→分镜→生图→图生视频→配音→音效→剪辑→质检发布
   输入契约锚定项目本地目录（init 脚手架生成，唯一真源）
L3 执行层 MCP 矩阵（见第四节）
L4 知识层（打包进 skill 本体 references/，随装随用）：
   drama-skills 方法论 + OpenMontage skill 知识 + LuxReal 提示词层
   + 私有实证（分层混合/3 抽/朝向图赢词/术语陷阱——工具行为知识，项目无关）
```

**init 脚手架**：`drama-studio init <项目名>` 生成：

```
<新项目>/
  drama.config.json        # 流水线配置：模型档位/成本预算（默认 100 元/集）/画风/音色映射
  剧本/EP-XXX.md           # 剧本（含台词钩子与人设底线标注）
  角色资产/                # 一致性源头：面部定稿图 + 服饰色盘 + voice_id 表
  分镜/EP-XXX.md           # 分镜表真源：镜号/景别/秒数/画面/台词/模式分诊/状态列
  关键帧/EP-XXX/SHOT-XXX.png   # 1728×2304（3:4）命名规范
  视频/EP-XXX/SHOT-XXX.mp4     # 图生视频原始产出
  配音/EP-XXX/SHOT-XXX.mp3     # 与镜号一一对应
  音效/EP-XXX/             # BGM + 音效素材
  成片/EP-XXX.mp4          # 最终输出
  质检/EP-XXX.md           # 各阶段质检门记录（3 抽结果/达标状态）
  manifest.json            # 流水线状态机检查点（OpenMontage 式）
```

各阶段只读写自己负责的目录；状态字段写在分镜表内，禁止第二套并行真相。

**与现有短剧技能家族的关系（终态架构）**：

- **双总入口切分**：drama-studio = 成片流水线总入口（生成执行+质检+成片，端到端编排）；`short-drama` = 创作文档工作台（项目文档管理/Dashboard/进度查看）。两者 description 互相划界——跨阶段"做成片"路由 drama-studio，跨阶段"管理创作文档"路由 short-drama。
- **协同机制（两轴）**：① 数据轴 = 目录真源交接——技能互不感知，靠 init 脚手架目录交接（write 产 `剧本/` → storyboard 读剧本产 `分镜/` → … → review 对照质检），各技能只读写自己目录；② 控制轴 = drama-studio SKILL.md 内置"阶段→子技能映射表"，主 agent 按流水线阶段调度子技能。
- **使用方式**：单环节需求直接开口（自动按 description 路由到子技能）；端到端成片走 drama-studio（按 manifest 逐阶段调度 + 质检门放行）。

| 层 | 技能 | 定位 | 动作 |
|---|------|------|------|
| 总入口·成片 | `drama-studio` | 端到端流水线编排 | P2 新建 |
| 总入口·文档 | `short-drama` | 创作文档工作台 | description 划界 |
| 前期 | `novel-analyze` / `develop` | 原著分析→改编方案/分集地图 | 原样保留 |
| 阶段 | `write` / `assets` / `storyboard` / `image-prompts` / `video-prompts` | 剧本/视觉设定/分镜/图片提示词/视频提示词 | P2 改造：注入私有质检门+工具实证 |
| 执行 | `produce` | 挂 MCP 三件套的生产执行器（付费确认安全门保留） | P2 重写 |
| 质检 | `review` | 全链路质检门（吸收 quality 合规/海外格式要点） | P2 改造 |
| 缺口 | 配音提示词 / 剪辑 / 音效（新建 3 个） | L2 缺失环节 | P2 新建 |
| 退役 | `knowhow` / `quality` | 维护者治理 / 与 write·review 重叠 | 内容吸收进 L4 后退役 |

**OpenMontage 流水线不能直接用**：其 12 条流水线为通用视频向（纪录片/广告），无竖屏短剧 30 镜×2-4s、台词 TTS 挂载、抽卡分诊结构——**吸收其 manifest/状态机/适配层模式，P1 真人短剧流水线需重写**。

---

## 四、L3 执行层 MCP 矩阵（成本双轨）

| 环节 | 短期（零新增配置） | 长期（API 化，账号前提已具备） | 状态 |
|------|---------------------------|---------------------|------|
| 剧本/文本生成 | ZCode 会话内直接生成 | 管线脚本调 MiniMax M3 / DeepSeek V4 API | ✅ |
| 文生图 | 即梦网页（基础会员积分，人工/CUA） | 火山方舟 doubao-seedream 生图 API（现成 MCP：nsmao-com/seedream-mcp，Seedream 5.0 系） | ⚠️ 现状/P2 |
| 图生视频 | CUA 操作即梦网页（复用会员积分；无 CLI） | **火山方舟 Seedance 2.0/2.5 API**（现成 MCP：leonaiuv/seedance-2-mcp——真 2.0 标准/fast、480-720p、4-15s、9:16、多图 9 张、音频模态输入；提交→轮询→产出落 `视频/EP-XXX/`，状态回写为自建补丁；两套钱，量大再切） | ⚠️ 现状/P1 |
| 配音 TTS | MiniMax/豆包网页+批量脚本半自动 | **豆包 TTS MCP**（2.8 元/万字符 [T1]；现成件：lxy2109/doubao-tts-mcp——音色映射/情感/语速/落盘，凭证走语音控制台 APPID/TOKEN） | 🔴 P1 |
| 音效 | 剪映音效库关键词表（手动） | ElevenLabs 官方 MCP（SFX v2）[海外网络/计费] | 🟡 P2/P3 |
| 字幕 | 剪映语音转字幕 | **faster-whisper 本地**（M3 Max 快，0 元，SRT） | 🟡 P2 |
| 剪辑合成 | 剪映手动（复杂特效） | **video-use**（文件夹+自然语言）+ kinocut/ffmpeg MCP（硬切/BGM/黑场自动化） | 🟡 P2 |
| **质感补丁** | 可灵网页手动补镜 | **可灵官方 MCP**（白名单镜批量多版本择优；Seedance 质感不达标时触发） | 🟡 P2 备选 |
| 备选配音 | — | Voicebox；GPT-SoVITS（Mac MPS 支持一般 [H]，第三备选） | P3 |

---

## 五、吸收清单（双底座 + 三吸收）

| 角色 | 选定 | 理由 |
|------|------|------|
| 底座 A：agent-native 骨架 | OpenMontage | 唯一 Claude Code skill 形态的全流程系统，54.8k 星 [F]；clone 独立目录运行，AGPLv3 |
| 底座 B：国内链参考实现 | LocalMiniDrama | Seedance 2+真人剧+开箱即用 [F 已核]；独立 app 非 MCP，ZCode 调度仍需 P1 自建 |
| 吸收 1：阶段分工设计 | ViMax | 导演/编剧/制片/生成器四角色 → L2 阶段 skill 角色化参考 |
| 吸收 2：电影级提示词层 | short-drama-skills（LuxReal） | 剧本→镜头序列→电影级视频提示词，直接并入 L4 |
| 吸收 3：环节执行器 | video-use / Voicebox / 豆包 TTS MCP / faster-whisper / 可灵官方 MCP | L3 矩阵 |

---

## 六、实施路线（总投入 3.5-4.5 天，不含学习调试缓冲 [H]）

**P0（1-1.5 天）——双底座对跑 + MCP 三件套装配验证**
0. 创建 `~/.zcode/skills/drama-studio/` 技能目录
1. OpenMontage **clone 到独立目录**（如 `~/tools/OpenMontage`）+ `make setup`（前置：Python 3.10+ / FFmpeg / Node 18+；预算含环境装配）
2. ZCode 适配：其 CLAUDE.md 引导转写为 AGENTS.md（官方兼容列表无 ZCode，需验证）
3. 装 LocalMiniDrama（GitHub xuanyustudio / 83zi.com），配火山 Key
4. 同一条 30 秒测试片双跑，评分维度：**通用可复用性（骨架可改造度）** / 短剧结构贴合度 / 国内链顺滑度 / 可控性
5. 同场加做（P1 步骤 5-6 前移）：MCP 三件套装配 + 真钱验证（<10 元；需提前备好方舟 `ARK_API_KEY` 与语音控制台 `VOLC_APPID`/`VOLC_TOKEN`）

**P1（1-1.5 天）——补执行断层（复用优先：现成社区 MCP + 缺口自建；步骤 5-6 若已于 P0 完成则跳过）**
5. 装配三件现成 MCP（凭证：视频/生图=方舟 `ARK_API_KEY`；配音=语音控制台 `VOLC_APPID`/`VOLC_TOKEN`）：
   - 视频 `leonaiuv/seedance-2-mcp`：真 Seedance 2.0（标准/fast），npx 一键装，stdio
   - 生图 `nsmao-com/seedream-mcp`：Seedream 5.0 系文生图+图生图，stdio/http 双模
   - 配音 `lxy2109/doubao-tts-mcp`：自然语言音色映射+情感+语速+落盘返回绝对路径
6. 真钱验证（预算 <10 元）：1 段 TTS + 1 镜 720p 视频 + 1 镜音频模态（验口型效果与真实计费）
7. 缺口自建（半天）：分镜表状态列回写、产出即时落盘（API 返回链接约 24h 过期）、本地素材公网化（优先方舟 asset 上传接口，fallback 本地 http 服务）
8. 并行：首部正式剧集剧本产出（MiniMax M3 + short-drama-write，写实友好题材）

**P2（1-2 天）——整合 drama-studio + 新项目首集实测**
9. 总入口 SKILL.md（评分选型+manifest 成本熔断 100 元默认）+ L4 知识打包（references/）+ init 脚手架 + 重写 P1 真人短剧流水线
10. 阶段技能族建设（改造现有为主+缺口新建）：改造 6 个阶段技能（`write`/`assets`/`storyboard`/`image-prompts`/`video-prompts`/`review`——注入私有质检门+工具实证，即知识回流）；重写 `produce` 为挂 MCP 三件套的执行器（保留付费确认门）；新建 3 个缺口技能（配音提示词/剪辑/音效）；`knowhow`/`quality` 内容吸收进 L4 后退役；`short-drama` description 与 drama-studio 互相划界
11. 全新项目首集全流程实测回修（`drama-studio init` 起步，day-one 本地真源）
12. （条件触发）Seedance 质感不达标 → 接可灵官方 MCP 补白名单镜

---

## 七、风险与边界

1. **两套钱风险**：方舟 API 按量计费独立于即梦会员——自动化便利 vs 重复付费，量小用 CUA，量大再切 API
2. **OpenMontage 装配预算**：Node/FFmpeg/Remotion 环境折腾可能超 1 天 [H]；**AGPLv3**——自用无碍，开源 drama-studio 需注意传染性 [F]
3. OpenMontage 偏海外模型链，国内链需自接；兼容列表无 ZCode，AGENTS.md 适配效果待 P0 验证
4. LocalMiniDrama 成熟度靠 P0 试用验证；ViMax 换国内 API 有适配成本 [H]
5. ElevenLabs 海外网络/计费，音效先剪映库兜底
6. 开源给骨架，**真人短剧垂直深度（抽卡分诊、分层混合、竖屏节奏）靠 L4 注入**——这是本方案与通用工具的本质差异
7. "$0.15/条 / 7 维评分"为单一来源 [T3]，P0 实测为准；口型音频模态效果与计费 P1 单镜验证后定推广范围
8. **发布规格**：关键帧 3:4（1728×2304）→ 竖屏 9:16 发布裁切策略在 P2 实测时定义（左移/居中/安全框）
9. **执行节奏**：P0-P2 需集中整段完成（P0 建议 1 天），碎片化易搁置
10. **社区 MCP 体量小**（3-16 星）维护性存疑 [H]；API 素材须公网 URL（本地关键帧需上传中转）、产出链接约 24h 过期——即时落盘与素材上传列为 P1 自建补丁；火山官方 mcp-server 仓库无 Seedance/豆包 TTS（媒体生成缺位，已核 [F 2026-08-31]）

---

## 📌 核心摘要

- 要点 1：drama-studio = 通用可复用技能——全局安装、init 脚手架生成新项目目录树、L4 私有实证打包进 skill 本体、飞书为可选镜像插件 [F]
- 要点 2：双底座+三吸收（OpenMontage 54.8k 星骨架 + LocalMiniDrama 国内链 + ViMax/LuxReal/执行器），投产主力 = 方舟底模 API + 自有 skill 编排 [F]
- 要点 3：成本熔断默认 100 元/集；口型双路线（白名单音频模态 / 量产后期 TTS）；3 抽纪律内建 [F]
- 要点 4：P0 双底座对跑+MCP 三件套装配验证 1-1.5 天 → P1 缺口自建（复用优先）→ P2 整合+新项目首集实测 1-2 天（总投入 3.5-4.5 天）[P]
- 要点 5：技能家族终态 = 双总入口切分（drama-studio 成片 / short-drama 文档）+ 6 改造 + produce 重写 + 3 新建 + 2 退役（knowhow/quality），协同靠目录真源交接 + 阶段映射调度 [F]
