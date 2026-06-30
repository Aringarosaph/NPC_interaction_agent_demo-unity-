using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

public class NpcDialogueClient : MonoBehaviour
{
    public string endpoint = "http://127.0.0.1:8008/api/v1/dialogue";
    public string sessionId = "local_session_001";
    public string playerId = "local_player";
    public SpeechBubbleController playerBubble;
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

        using (var req = new UnityWebRequest(endpoint, "POST"))
        {
            req.uploadHandler = new UploadHandlerRaw(body);
            req.downloadHandler = new DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");

            yield return req.SendWebRequest();

            if (req.result != UnityWebRequest.Result.Success)
            {
                lastError = $"{req.error} / {req.downloadHandler.text}";
                Debug.LogError($"NPC dialogue failed: {lastError}");
                yield break;
            }

            var resp = JsonUtility.FromJson<DialogueResponseDto>(req.downloadHandler.text);
            if (resp == null || resp.utterances == null)
            {
                lastError = $"NPC dialogue returned an invalid response: {req.downloadHandler.text}";
                Debug.LogError(lastError);
                yield break;
            }
            lastResponse = resp;

            var bubble = npc.bubbleAnchor != null ? npc.bubbleAnchor.GetComponentInChildren<SpeechBubbleController>() : npc.GetComponentInChildren<SpeechBubbleController>();
            foreach (var utt in resp.utterances)
            {
                float delay = Mathf.Max(0f, utt.delay_ms / 1000f);
                yield return new WaitForSeconds(delay);
                if (bubble != null) bubble.Show(utt.text, npcBubbleSeconds);
                Debug.Log($"{npc.displayName}: {utt.text} emotion={utt.emotion} action={utt.action} used_knowledge_ids={JoinIds(resp.@internal != null ? resp.@internal.used_knowledge_ids : null)}");
                yield return new WaitForSeconds(npcBubbleSeconds * 0.65f);
            }
        }
    }

    private static string JoinIds(System.Collections.Generic.List<string> ids)
    {
        if (ids == null || ids.Count == 0) return "[]";
        return "[" + string.Join(", ", ids) + "]";
    }
}
