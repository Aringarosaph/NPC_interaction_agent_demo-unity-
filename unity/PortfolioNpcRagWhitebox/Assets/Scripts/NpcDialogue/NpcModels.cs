using System;
using System.Collections.Generic;

[Serializable]
public class DialogueWorldState
{
    public string location_id = "portfolio_whitebox_room";
    public string game_time_label = "demo";
    public int quest_stage = 0;
    public float relationship_score = 0f;
    public bool debug_enabled = true;
}

[Serializable]
public class DialogueRequestDto
{
    public string schema_version = "dialogue_request.v1";
    public string session_id;
    public string player_id = "local_player";
    public string npc_id;
    public string player_text;
    public float distance_m;
    public bool is_in_range;
    public DialogueWorldState world_state = new DialogueWorldState();
}

[Serializable]
public class DialogueResponseDto
{
    public string schema_version;
    public string turn_id;
    public string npc_id;
    public List<UtteranceDto> utterances;
    public InternalDebugDto @internal;
}

[Serializable]
public class UtteranceDto
{
    public string text;
    public string emotion;
    public string action;
    public int delay_ms;
}

[Serializable]
public class InternalDebugDto
{
    public List<string> used_knowledge_ids;
    public List<string> used_memory_ids;
    public float confidence;
}

[Serializable]
public class DialogueResponseV2Dto
{
    public string schema_version;
    public string turn_id;
    public string npc_id;
    public List<UtteranceDto> utterances;
    public List<WorldEventDto> world_events;
    public AgentTraceDto trace;
}

[Serializable]
public class AgentPlanDto
{
    public string intent;
    public string goal;
    public List<string> required_knowledge;
    public List<string> proposed_tools;
    public List<string> risk_flags;
    public string public_reason;
}

[Serializable]
public class ToolCallDto
{
    public string call_id;
    public string tool_name;
    public ToolArgumentsDto arguments;
    public string reason;
}

[Serializable]
public class ToolArgumentsDto
{
    public string quest_id;
    public int expected_stage;
    public float delta;
    public string reason;
    public string item_id;
    public int quantity;
    public string event_type;
    public WorldEventPayloadDto payload;
    public bool player_visible;
}

[Serializable]
public class ToolResultDto
{
    public string call_id;
    public string tool_name;
    public bool ok;
    public ToolResultPayloadDto result;
    public string error;
}

[Serializable]
public class ToolResultPayloadDto
{
    public string quest_id;
    public int stage;
    public string status;
    public float relationship_score;
    public string relationship_label;
    public float delta;
    public string item_id;
    public int quantity;
    public int total_quantity;
    public WorldEventDto world_event;
}

[Serializable]
public class WorldEventDto
{
    public string event_id;
    public string event_type;
    public WorldEventPayloadDto payload;
    public bool player_visible;
}

[Serializable]
public class WorldEventPayloadDto
{
    public string quest_id;
    public int stage;
    public string status;
    public float relationship_score;
    public string relationship_label;
    public float delta;
    public string item_id;
    public int quantity;
    public int total_quantity;
}

[Serializable]
public class AgentTraceDto
{
    public List<string> used_knowledge_ids;
    public List<string> used_memory_ids;
    public AgentPlanDto plan;
    public List<ToolCallDto> tool_calls;
    public List<ToolResultDto> tool_results;
    public List<MemoryCandidateDto> memory_candidates;
    public ReflectionDto reflection;
    public float confidence;
}

[Serializable]
public class MemoryCandidateDto
{
    public string memory_id;
    public string memory_type;
    public string summary;
    public string detail;
    public float salience;
}

[Serializable]
public class ReflectionDto
{
    public string failure_reason;
    public string corrective_hint;
}
