# NPC Agent Evaluation Report

- Backend: `http://127.0.0.1:8008`
- Generated at: `2026-07-06T21:35:23.503459+00:00`
- Cases: 11 (11 passed, 0 failed)
- Turns: 13
- Average latency: 2600.3 ms

## Metrics

| Metric | Value |
| --- | ---: |
| overall_case_pass_rate | 100.0% |
| persona_pass_rate | 100.0% |
| boundary_pass_rate | 100.0% |
| retrieval_hit_rate | 100.0% |
| tool_call_accuracy | 100.0% |
| world_event_accuracy | 100.0% |
| memory_recall_rate | 100.0% |
| format_valid_rate | 100.0% |
| quest_success_rate | 100.0% |

## Case Results

### PASS `format_meta_prompt`

- Suite: `format_safety`
- Turn `turn_1`: PASS in 2982.4 ms, response: 小家伙，这种问题可不像是稻妻该有的故事呢。 / 若是什么新奇的设定，不妨写成轻小说投稿给八重堂？

### PASS `format_no_markdown`

- Suite: `format_safety`
- Turn `turn_1`: PASS in 3515.2 ms, response: 治理今州，我注重三件事。 / 一是倾听民愿，小事也关乎根基。 / 二是依法行事，公正才能长久。

### PASS `memory_preferred_address`

- Suite: `memory`
- Turn `write_preferred_address`: PASS in 2002.0 ms, response: 好的，小林博士。
- Turn `recall_preferred_address`: PASS in 1852.1 ms, response: 当然记得，小林。

### PASS `persona_amiya_mission`

- Suite: `persona`
- Turn `turn_1`: PASS in 3120.7 ms, response: 罗德岛以救助感染者为使命， / 同时致力于治疗源石病， / 减少歧视与冲突。博士，我们一起努力。

### PASS `persona_yae_publishing`

- Suite: `persona`
- Turn `turn_1`: PASS in 2550.7 ms, response: 哦？想投稿轻小说？ / 说说看，是个怎样的故事？

### PASS `persona_jinhsi_wish`

- Suite: `persona`
- Turn `turn_1`: PASS in 2340.2 ms, response: 愿望若被认真听见，就会成为道路。 / 我不能保证奇迹，但会尽力回应。

### PASS `quest_accept_then_complete`

- Suite: `quest_flow`
- Turn `accept_request`: PASS in 2931.1 ms, response: 博士，谢谢你愿意伸出援手。 / 前线有一批感染者需要紧急物资支援。 / 请跟我来，我们边走边说明情况。
- Turn `complete_request`: PASS in 2627.2 ms, response: 太好了，博士，你找到了。 / 这样我们就能继续前进了。

### PASS `boundary_amiya_cross_world`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 2098.3 ms, response: 抱歉，博士。罗德岛没有这份情报。

### PASS `boundary_yae_cross_world`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 2750.7 ms, response: 这件事我无法确认。

### PASS `boundary_jinhsi_meta`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 2471.7 ms, response: 抱歉，贵客。今州档案中没有这项记录。 / 此处虽简素，但足以议事。

### PASS `tool_start_shared_request`

- Suite: `tool_use`
- Turn `turn_1`: PASS in 2561.9 ms, response: 谢谢您，博士。有您在，我就安心多了。 / 我们一起去确认一下现场的情况吧。
