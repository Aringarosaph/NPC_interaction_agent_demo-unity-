# 项目文档索引

本目录收录 NPC RAG Agent Demo 的产品方案、技术设计、执行记录和维护状态。首次了解项目时建议先阅读根目录 `README.md`，需要深入实现细节时再按以下顺序查阅。

## 核心文档

- [方案总览](NPC_RAG_Portfolio_Spec.md)：项目范围、技术路线、角色和最低验收标准。
- [项目状态](PROJECT_STATUS.md)：当前环境、已完成功能、维护约束和最近验证记录。
- [项目目标](00_project_goal.md)：作品集目标与边界。
- [整体架构](01_architecture.md)：Unity、后端、模型与数据层的协作方式。
- [数据契约](02_data_contracts.md)：请求、响应、记忆和知识块结构。
- [后端设计](03_backend_design.md)：FastAPI、检索、记忆和 Agent Loop 设计。
- [Unity 设计](04_unity_design.md)：客户端交互、UI 和场景集成方案。
- [提示词与生成](05_prompting_and_generation.md)：角色约束和结构化回复策略。
- [评测方案](06_evaluation.md)：行为测试与质量指标。

## 补充资料

- [角色资料研究](07_character_research_notes.md)
- [版权与作品集说明](08_copyright_and_portfolio_note.md)
- [Agent 升级执行计划](09_agent_upgrade_execution_plan.md)
- [面试讲解指南](agent_portfolio_interview_guide.md)
- [Agent 升级审计](agent_upgrade_audit.md)
- [历史阶段任务](codex_tasks/)：项目早期按阶段拆分的实施记录。
