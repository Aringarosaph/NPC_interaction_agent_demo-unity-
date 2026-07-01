using UnityEngine;
using TMPro;

public class DialogueRangeDetector : MonoBehaviour
{
    public Transform player;
    public TMP_Text currentNpcLabel;

    public NpcAgentMarker CurrentNpc { get; private set; }
    public float CurrentDistance { get; private set; }

    private NpcAgentMarker[] npcs;

    private void Start()
    {
        npcs = FindObjectsByType<NpcAgentMarker>(FindObjectsInactive.Exclude);
    }

    private void Update()
    {
        CurrentNpc = null;
        CurrentDistance = float.MaxValue;
        if (player == null) return;
        if (npcs == null || npcs.Length == 0)
        {
            npcs = FindObjectsByType<NpcAgentMarker>(FindObjectsInactive.Exclude);
        }

        foreach (var npc in npcs)
        {
            if (npc == null) continue;
            float d = Vector3.Distance(player.position, npc.RangeCenterPosition);
            if (d <= npc.interactionRadius && d < CurrentDistance)
            {
                CurrentNpc = npc;
                CurrentDistance = d;
            }
        }

        if (currentNpcLabel != null)
        {
            currentNpcLabel.text = CurrentNpc == null ? "未进入 NPC 对话范围" : $"当前 NPC: {CurrentNpc.displayName}";
        }
    }
}
