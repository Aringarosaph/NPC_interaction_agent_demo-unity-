using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public class NpcDialogueClient : MonoBehaviour
{
    public string endpoint = "http://127.0.0.1:8008/api/dialogue";
    public string sessionId = "local_session_001";
    public string playerId = "local_player";
    public SpeechBubbleController playerBubble;
    public AgentDebugPanelController agentDebugPanel;
    public float npcBubbleSeconds = 2.4f;

    [System.NonSerialized] public DialogueResponseDto lastResponse;
    [System.NonSerialized] public string lastError;

    public IEnumerator SendToNpc(NpcAgentMarker npc, float distance, string playerText)
    {
        if (npc == null || string.IsNullOrWhiteSpace(playerText)) yield break;
        lastResponse = null;
        lastError = null;

        if (playerBubble != null)
        {
            playerBubble.Show(playerText, 2.0f);
        }

        var dto = new DialogueRequestDto
        {
            session_id = sessionId,
            player_id = playerId,
            npc_id = npc.npcId,
            player_text = playerText,
            distance_m = distance,
            is_in_range = true
        };

        string json = JsonUtility.ToJson(dto);
        byte[] body = Encoding.UTF8.GetBytes(json);

        yield return SendRequest(body);
        if (lastResponse == null)
        {
            yield break;
        }

        if (agentDebugPanel != null) agentDebugPanel.ApplyResponse(lastResponse);
        yield return ShowUtterances(
            npc,
            lastResponse.utterances,
            BuildDebugSummary(lastResponse)
        );
    }

    private IEnumerator SendRequest(byte[] body)
    {
        using (var req = CreateRequest(endpoint, body))
        {
            yield return req.SendWebRequest();

            if (req.result != UnityWebRequest.Result.Success)
            {
                lastError = $"{req.error} / {req.downloadHandler.text}";
                Debug.LogError($"NPC dialogue failed: {lastError}");
                yield break;
            }

            var resp = JsonUtility.FromJson<DialogueResponseDto>(req.downloadHandler.text);
            if (resp == null || resp.utterances == null || resp.trace == null)
            {
                lastError = $"NPC dialogue returned an invalid response: {req.downloadHandler.text}";
                Debug.LogError(lastError);
                yield break;
            }
            lastResponse = resp;
        }
    }

    private static UnityWebRequest CreateRequest(string url, byte[] body)
    {
        var req = new UnityWebRequest(url, "POST");
        req.uploadHandler = new UploadHandlerRaw(body);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");
        return req;
    }

    private IEnumerator ShowUtterances(NpcAgentMarker npc, System.Collections.Generic.List<UtteranceDto> utterances, string debugSummary)
    {
        var bubble = npc.bubbleAnchor != null ? npc.bubbleAnchor.GetComponentInChildren<SpeechBubbleController>() : npc.GetComponentInChildren<SpeechBubbleController>();
        foreach (var utt in utterances)
        {
            float delay = Mathf.Max(0f, utt.delay_ms / 1000f);
            yield return new WaitForSeconds(delay);
            if (bubble != null) bubble.Show(utt.text, npcBubbleSeconds);
            Debug.Log($"{npc.displayName}: {utt.text} emotion={utt.emotion} action={utt.action} {debugSummary}");
            yield return new WaitForSeconds(npcBubbleSeconds * 0.65f);
        }
    }

    private static string BuildDebugSummary(DialogueResponseDto resp)
    {
        if (resp == null || resp.trace == null)
        {
            return "trace=[]";
        }
        string intent = resp.trace.plan != null ? resp.trace.plan.intent : "none";
        int toolCount = resp.trace.tool_calls != null ? resp.trace.tool_calls.Count : 0;
        int eventCount = resp.world_events != null ? resp.world_events.Count : 0;
        return $"intent={intent} tool_calls={toolCount} world_events={eventCount} used_knowledge_ids={JoinIds(resp.trace.used_knowledge_ids)}";
    }

    private static string JoinIds(System.Collections.Generic.List<string> ids)
    {
        if (ids == null || ids.Count == 0) return "[]";
        return "[" + string.Join(", ", ids) + "]";
    }
}
