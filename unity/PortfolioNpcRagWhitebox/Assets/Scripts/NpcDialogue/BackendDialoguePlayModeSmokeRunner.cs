using System;
using System.Collections;
using UnityEngine;

public class BackendDialoguePlayModeSmokeRunner : MonoBehaviour
{
    private const string TargetNpcId = "arknights_amiya";
    private const string SmokePrompt = "阿米娅，请回应一次 Unity 联调测试。";

    public IEnumerator Run(Action<bool, string> complete)
    {
        yield return null;

        NpcAgentMarker npc = FindNpc(TargetNpcId);
        if (npc == null)
        {
            complete(false, $"NPC marker with id {TargetNpcId} was not found.");
            yield break;
        }

        NpcDialogueClient client = UnityEngine.Object.FindAnyObjectByType<NpcDialogueClient>();
        if (client == null)
        {
            complete(false, "Dialogue client is missing.");
            yield break;
        }

        client.sessionId = "unity_playmode_smoke_" + Guid.NewGuid().ToString("N");
        client.playerId = "unity_playmode_smoke";
        client.npcBubbleSeconds = 0.15f;

        yield return client.SendToNpc(npc, 1.2f, SmokePrompt);

        DialogueResponseDto response = client.lastResponse;
        if (!string.IsNullOrEmpty(client.lastError))
        {
            complete(false, client.lastError);
            yield break;
        }
        if (response == null || response.npc_id != npc.npcId || response.utterances == null || response.utterances.Count == 0)
        {
            complete(false, "Unity received an empty or mismatched dialogue response.");
            yield break;
        }

        complete(true, $"{npc.displayName} replied: {response.utterances[0].text}");
    }

    private static NpcAgentMarker FindNpc(string npcId)
    {
        NpcAgentMarker[] npcs = UnityEngine.Object.FindObjectsByType<NpcAgentMarker>(FindObjectsInactive.Exclude, FindObjectsSortMode.None);
        foreach (NpcAgentMarker npc in npcs)
        {
            if (npc != null && npc.npcId == npcId)
            {
                return npc;
            }
        }
        return null;
    }
}
