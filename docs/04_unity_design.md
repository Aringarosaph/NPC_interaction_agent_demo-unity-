# 04 Unity 白盒接入设计

## 场景结构

```text
Scene_PortfolioNpcRag
  ├─ PlayerCapsule
  │   ├─ PlayerController
  │   ├─ PlayerChatInput
  │   └─ BubbleAnchor
  ├─ NPC_Amiya_Capsule
  │   ├─ NpcAgentMarker(npc_id=arknights_amiya)
  │   └─ BubbleAnchor
  ├─ NPC_YaeMiko_Capsule
  │   ├─ NpcAgentMarker(npc_id=genshin_yae_miko)
  │   └─ BubbleAnchor
  ├─ NPC_Jinhsi_Capsule
  │   ├─ NpcAgentMarker(npc_id=wuwa_jinhsi)
  │   └─ BubbleAnchor
  ├─ Canvas
  │   ├─ InputField/TMP_InputField
  │   ├─ SendButton
  │   └─ CurrentNpcLabel
  └─ DialogueSystem
      ├─ DialogueRangeDetector
      ├─ NpcDialogueClient
      └─ SpeechBubbleController
```

## 交互规则

- 玩家与 NPC 距离 <= `interaction_radius_m` 时可对话。
- 多个 NPC 同时在范围内时选最近的。
- 没有 NPC 在范围内时，发送按钮不可用或显示提示。
- 玩家发送后，玩家气泡立即显示。
- 后端返回后，NPC 按 `utterances[i].delay_ms` 逐句显示。

## UI 简化建议

作品集不需要美术：

- NPC 用 Capsule 或 Cube。
- 每个 NPC 头上放名字文本。
- 气泡用世界空间 Canvas + TextMeshPro。
- 不做表情模型，只用 `emotion` 改气泡小标签或 Debug 文本。
- `action` 可先只 Debug.Log，后期再绑定点头/转身动画。

## HTTP 方案

MVP 使用普通 POST：

```text
POST http://127.0.0.1:8008/api/v1/dialogue
```

收到完整 JSON 后本地逐句播放。这样不会被 SSE 解析、跨平台差异、缓冲问题拖慢。

## 可选升级

录屏效果稳定后，再做：

- NPC 输入中 “...” 气泡。
- 每句字打字机效果。
- SSE 流式响应。
- 根据 emotion 切换气泡边框或动作。
