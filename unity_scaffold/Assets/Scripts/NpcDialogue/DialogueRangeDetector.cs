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
        npcs = FindObjectsOfType<NpcAgentMarker>();
    }

    private void Update()
    {
        CurrentNpc = null;
        CurrentDistance = float.MaxValue;
        foreach (var npc in npcs)
        {
            float d = Vector3.Distance(player.position, npc.transform.position);
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
