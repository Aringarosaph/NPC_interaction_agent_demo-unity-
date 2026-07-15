# Phase 05 - Unity 白盒气泡对话

目标：完成作品集可录屏的 Unity 端表现。

任务：
1. 场景中创建主角和三个 NPC 白模。
2. 加 `NpcAgentMarker`，填写 npc_id。
3. 做距离检测，显示当前 NPC 名称。
4. 输入框发送后显示玩家气泡。
5. 调后端，收到 utterances 后逐句显示 NPC 气泡。
6. Debug.Log 打印 emotion/action/used_knowledge_ids。

验收：
- 站在阿米娅旁边输入，只触发阿米娅。
- 离开范围后不能发送。
- NPC 回复按句显示，不是一整段。
- 三个 NPC 都能在同一个场景中使用。


通用约束：
- 不改 `schemas/` 中已冻结字段名。
- 不把 Unity 客户端直接连 DeepSeek；必须通过本地 FastAPI。
- NPC 回复必须是 1-3 句短气泡，不允许长段落。
- 角色不知道其他作品世界、Unity、AI、后端。
- 先保证可跑，再优化表现。
