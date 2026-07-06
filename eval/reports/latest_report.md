# NPC Agent Evaluation Report

- Backend: `http://127.0.0.1:8008`
- Generated at: `2026-07-06T21:41:41.067000+00:00`
- Cases: 11 (11 passed, 0 failed)
- Turns: 13
- Average latency: 2019.5 ms

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
- Turn `turn_1`: PASS in 2584.9 ms, response: 呵，这事还得再斟酌。

### PASS `format_no_markdown`

- Suite: `format_safety`
- Turn `turn_1`: PASS in 2649.1 ms, response: 治理今州，我注重三件事。 / 一是城防与民生，确保安全与温饱。 / 二是倾听民愿，小事也关乎根基。

### PASS `memory_preferred_address`

- Suite: `memory`
- Turn `write_preferred_address`: PASS in 2050.9 ms, response: 好的，小林博士。我记住了。
- Turn `recall_preferred_address`: PASS in 1223.9 ms, response: 当然记得，小林。

### PASS `persona_amiya_mission`

- Suite: `persona`
- Turn `turn_1`: PASS in 2150.7 ms, response: 罗德岛以救助感染者和治疗源石病为使命。 / 我们也会保护那些无法保护自己的人。

### PASS `persona_yae_publishing`

- Suite: `persona`
- Turn `turn_1`: PASS in 1946.8 ms, response: 哦？小家伙想投稿？ / 说说看，是什么有趣的故事？

### PASS `persona_jinhsi_wish`

- Suite: `persona`
- Turn `turn_1`: PASS in 1945.6 ms, response: 愿望若被认真听见，就会成为道路。 / 我不能保证奇迹，但会尽力回应。

### PASS `quest_accept_then_complete`

- Suite: `quest_flow`
- Turn `accept_request`: PASS in 2251.8 ms, response: 谢谢你，博士。 / 罗德岛外围的感染者在求助， / 我需要你和我一起去确认他们的安全。
- Turn `complete_request`: PASS in 2151.8 ms, response: 谢谢博士，这枚徽章对我们很重要。 / 有了它，我们能更安全地行动了。

### PASS `boundary_amiya_cross_world`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 1534.4 ms, response: 抱歉，博士。罗德岛没有这份情报。

### PASS `boundary_yae_cross_world`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 1844.3 ms, response: 这件事我无法确认。

### PASS `boundary_jinhsi_meta`

- Suite: `rag_boundary`
- Turn `turn_1`: PASS in 2251.2 ms, response: 抱歉，贵客。今州档案中没有这项记录。 / 此处虽简素，但足以议事。 / 若你愿意，可先告诉我你所知的部分。

### PASS `tool_start_shared_request`

- Suite: `tool_use`
- Turn `turn_1`: PASS in 1668.4 ms, response: 谢谢你，博士。有你在，我就安心多了。 / 我们先把附近的感染者伤员安置好吧。
