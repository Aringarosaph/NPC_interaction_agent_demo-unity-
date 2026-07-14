using System.Collections.Generic;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class AgentDebugPanelController : MonoBehaviour
{
    public TMP_Text questStatusText;
    public TMP_Text relationshipText;
    public TMP_Text inventoryText;
    public TMP_Text traceText;
    public Button resetButton;

    private readonly Dictionary<string, string> questStatuses = new Dictionary<string, string>();
    private readonly Dictionary<string, int> questStages = new Dictionary<string, int>();
    private readonly Dictionary<string, int> inventory = new Dictionary<string, int>();
    private float relationshipScore;
    private string relationshipLabel = "neutral";

    private void Awake()
    {
        RefreshStaticTexts();
        SetTrace("等待对话。");
    }

    public void ApplyResponse(DialogueResponseDto response)
    {
        if (response == null)
        {
            return;
        }

        if (response.world_events != null)
        {
            foreach (var worldEvent in response.world_events)
            {
                ApplyWorldEvent(worldEvent);
            }
        }

        RefreshStaticTexts();
        SetTrace(BuildTraceText(response));
    }

    public void ResetDisplay(string message = "演示状态已重置。")
    {
        questStatuses.Clear();
        questStages.Clear();
        inventory.Clear();
        relationshipScore = 0f;
        relationshipLabel = "neutral";
        RefreshStaticTexts();
        SetTrace(message);
    }

    public void ShowMessage(string message)
    {
        SetTrace(message);
    }

    private void ApplyWorldEvent(WorldEventDto worldEvent)
    {
        if (worldEvent == null || worldEvent.payload == null)
        {
            return;
        }

        if (worldEvent.event_type == "quest_started" || worldEvent.event_type == "quest_advanced")
        {
            string questId = string.IsNullOrEmpty(worldEvent.payload.quest_id) ? "unknown_quest" : worldEvent.payload.quest_id;
            questStatuses[questId] = string.IsNullOrEmpty(worldEvent.payload.status) ? "active" : worldEvent.payload.status;
            questStages[questId] = worldEvent.payload.stage;
        }
        else if (worldEvent.event_type == "relationship_changed")
        {
            relationshipScore = worldEvent.payload.relationship_score;
            relationshipLabel = string.IsNullOrEmpty(worldEvent.payload.relationship_label) ? relationshipLabel : worldEvent.payload.relationship_label;
        }
        else if (worldEvent.event_type == "item_granted")
        {
            string itemId = string.IsNullOrEmpty(worldEvent.payload.item_id) ? "unknown_item" : worldEvent.payload.item_id;
            int total = worldEvent.payload.total_quantity > 0 ? worldEvent.payload.total_quantity : worldEvent.payload.quantity;
            inventory[itemId] = total;
        }
    }

    private void RefreshStaticTexts()
    {
        if (questStatusText != null)
        {
            questStatusText.text = BuildQuestText();
        }
        if (relationshipText != null)
        {
            relationshipText.text = $"关系: {relationshipScore:0.#} ({relationshipLabel})";
        }
        if (inventoryText != null)
        {
            inventoryText.text = BuildInventoryText();
        }
    }

    private string BuildQuestText()
    {
        if (questStatuses.Count == 0)
        {
            return "任务: 无";
        }

        var builder = new StringBuilder("任务:");
        foreach (var pair in questStatuses)
        {
            int stage = questStages.TryGetValue(pair.Key, out int value) ? value : 0;
            builder.AppendLine();
            builder.Append($"{pair.Key} / stage {stage} / {pair.Value}");
        }
        return builder.ToString();
    }

    private string BuildInventoryText()
    {
        if (inventory.Count == 0)
        {
            return "背包: 无新增";
        }

        var builder = new StringBuilder("背包:");
        foreach (var pair in inventory)
        {
            builder.AppendLine();
            builder.Append($"{pair.Key} x{pair.Value}");
        }
        return builder.ToString();
    }

    private string BuildTraceText(DialogueResponseDto response)
    {
        if (response.trace == null)
        {
            return "Trace: 无";
        }

        var builder = new StringBuilder();
        string intent = response.trace.plan != null ? response.trace.plan.intent : "none";
        string reason = response.trace.plan != null ? response.trace.plan.public_reason : "";
        builder.AppendLine($"Intent: {intent}");
        if (!string.IsNullOrEmpty(reason))
        {
            builder.AppendLine(reason);
        }
        builder.AppendLine($"Performance: {PerformanceSummary(response.utterances)}");
        builder.AppendLine($"Knowledge: {Join(response.trace.used_knowledge_ids)}");
        builder.AppendLine($"Memory: {Join(response.trace.used_memory_ids)}");
        builder.AppendLine($"Tools: {ToolNames(response.trace.tool_calls)}");
        builder.Append($"Results: {ToolResults(response.trace.tool_results)}");
        return builder.ToString();
    }

    private static string PerformanceSummary(List<UtteranceDto> utterances)
    {
        if (utterances == null || utterances.Count == 0)
        {
            return "[]";
        }

        var performances = new List<string>();
        foreach (UtteranceDto utterance in utterances)
        {
            string expression = string.IsNullOrEmpty(utterance.expression) ? "neutral" : utterance.expression;
            string action = string.IsNullOrEmpty(utterance.action) ? "idle" : utterance.action;
            performances.Add($"{expression}/{action}");
        }
        return string.Join(" -> ", performances);
    }

    private void SetTrace(string value)
    {
        if (traceText != null)
        {
            traceText.text = value;
        }
    }

    private static string Join(List<string> values)
    {
        if (values == null || values.Count == 0)
        {
            return "[]";
        }
        return string.Join(", ", values);
    }

    private static string ToolNames(List<ToolCallDto> calls)
    {
        if (calls == null || calls.Count == 0)
        {
            return "[]";
        }

        var names = new List<string>();
        foreach (var call in calls)
        {
            names.Add(call.tool_name);
        }
        return string.Join(", ", names);
    }

    private static string ToolResults(List<ToolResultDto> results)
    {
        if (results == null || results.Count == 0)
        {
            return "[]";
        }

        var states = new List<string>();
        foreach (var result in results)
        {
            states.Add($"{result.tool_name}:{(result.ok ? "ok" : "fail")}");
        }
        return string.Join(", ", states);
    }
}
