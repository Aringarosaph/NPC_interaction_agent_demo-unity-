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
    public InternalDebugDto internal;
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
