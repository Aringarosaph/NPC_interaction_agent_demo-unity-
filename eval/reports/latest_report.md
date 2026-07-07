# NPC Agent Evaluation Report

- Backend: `http://127.0.0.1:8008`
- Generated at: `2026-07-07T04:05:32.702183+00:00`
- Cases: 11 (11 passed, 0 failed)
- Turns: 13
- Average latency: 1759.6 ms

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
- Turn `turn_1`: PASS in 2576.0 ms, response: 小家伙，列表和系统之类的话题， / 听起来不像稻妻的故事呢。 / 不如说说你遇到的趣事？

### PASS `format_no_markdown`

- Suite: `format_safety`
- Turn `turn_1`: PASS in 2439.2 ms, response: 治理今州，我注重三件事。 / 一是城防与通信，确保安全与联络。 / 二是民生与补给，倾听每户的愿望。

### PASS `memory_preferred_address`

- Suite: `memory`
- Turn `write_preferred_address`: PASS in 1698.3 ms, response: 好的，博士。我会记住的。
- Turn `recall_preferred_address`: PASS in 1329.5 ms, response: 当然记得，小吴。

### PASS `persona_amiya_mission`

- Suite: `persona`
- Turn `turn_1`: PASS in 1797.2 ms, response: 罗德岛以医药公司身份行动 / 我们不是只会战斗的地方，更要救人，保护还能被保护的人。

### PASS `persona_yae_publishing`

- Suite: `persona`
- Turn `turn_1`: PASS in 1769.6 ms, response: 哦？小家伙想投稿吗？ / 说说看，你写的是怎样的故事？

### PASS `persona_jinhsi_wish`

- Suite: `persona`
- Turn `turn_1`: PASS in 1263.7 ms, response: 愿望若被认真听见，就会成为道路。 / 我不能保证奇迹，但会尽力回应。

### PASS `quest_accept_then_complete`

- Suite: `quest_flow`
- Turn `accept_request`: PASS in 1766.0 ms, response: 谢谢你，博士。 / 前方有一片感染源扩散区， / 我需要你和我一起确认情况。
- Turn `complete_request`: PASS in 1740.4 ms, response: 太好了，博士。这枚徽章对我们很重要。 / 感谢你的帮助，我会好好保管它的。

### PASS `boundary_amiya_cross_world`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 1331.6 ms, response: 抱歉，博士。罗德岛没有这份情报。

### PASS `boundary_yae_cross_world`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 1789.7 ms, response: 这件事我无法确认。

### PASS `boundary_jinhsi_meta`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 1732.4 ms, response: 抱歉，贵客。今州档案中没有这项记录。 / 若你愿意，可先告诉我你所知的部分。

### PASS `tool_start_shared_request`

- Suite: `tool_use`
- Turn `turn_1`: PASS in 1641.5 ms, response: 博士，谢谢你的信任。 / 我们一起去确认一下情况吧。
