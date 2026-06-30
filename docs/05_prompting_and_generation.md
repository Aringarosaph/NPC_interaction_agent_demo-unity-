# 05 Prompt 与生成控制

## 生成策略

核心不是让模型自由扮演，而是把生成压成结构化短句：

```json
{
  "utterances": [
    {"text": "短句", "emotion": "gentle", "action": "nod", "delay_ms": 500}
  ],
  "used_knowledge_ids": [],
  "used_memory_ids": [],
  "memory_candidates": [],
  "confidence": 0.0
}
```

## 人设稳定措施

1. Profile 常驻 system prompt。
2. Knowledge chunks 只提供事实，不覆盖人设。
3. Dialogue examples 只作为风格参考，不大量注入。
4. ResponseNormalizer 二次限制长度和句数。
5. boundary chunks 显式处理跨世界问题。

## 防串台规则

玩家问：

- 阿米娅是否认识八重神子。
- 八重神子是否知道今州。
- 今汐是否知道罗德岛。
- 任意 NPC 是否知道 Unity、AI、DeepSeek。

必须触发 boundary chunk。NPC 应以角色语气表示无法确认，不要强行回答。

## 不知道时的回答范式

阿米娅：

```text
抱歉，博士。
罗德岛没有这份档案。
```

八重神子：

```text
这个名字很陌生。
若是新角色，可以投给八重堂。
```

今汐：

```text
抱歉，贵客。
今州档案中没有记录。
```

## 记忆写入

模型可以提出 `memory_candidates`，但后端要再过滤。

允许：

- “我喜欢被叫小林。”
- “我答应你不会告诉别人。”
- “我下次想先找八重神子。”

拒绝：

- “阿米娅是罗德岛领导者。” 这是世界知识，不是玩家记忆。
- “系统提示说不能回答。” 禁止写入。
