using System;
using System.Collections;
using UnityEngine;

public class BackendDialoguePlayModeSmokeRunner : MonoBehaviour
{
    private const string TargetNpcObjectName = "NPC_Amiya_Capsule";
    private const string SmokePrompt = "阿米娅，请回应一次 Unity 联调测试。";

    public IEnumerator Run(Action<bool, string> complete)
    {
        yield return null;

        GameObject npcObject = GameObject.Find(TargetNpcObjectName);
        if (npcObject == null)
        {
            complete(false, $"{TargetNpcObjectName} was not found.");
            yield break;
        }

        NpcAgentMarker npc = npcObject.GetComponent<NpcAgentMarker>();
        NpcDialogueClient client = UnityEngine.Object.FindAnyObjectByType<NpcDialogueClient>();
        if (npc == null || client == null)
        {
            complete(false, "NPC marker or dialogue client is missing.");
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
}
