using UnityEngine;
using UnityEngine.UI;
using TMPro;

public class PlayerChatInput : MonoBehaviour
{
    public TMP_InputField inputField;
    public Button sendButton;
    public DialogueRangeDetector rangeDetector;
    public NpcDialogueClient dialogueClient;

    private void Start()
    {
        if (sendButton != null) sendButton.onClick.AddListener(Send);
        if (inputField != null) inputField.onSubmit.AddListener(_ => Send());
    }

    private void Update()
    {
        if (sendButton != null)
        {
            sendButton.interactable = rangeDetector != null && rangeDetector.CurrentNpc != null;
        }
    }

    public void Send()
    {
        if (rangeDetector == null || dialogueClient == null || inputField == null) return;
        var npc = rangeDetector.CurrentNpc;
        if (npc == null) return;
        string text = inputField.text.Trim();
        if (string.IsNullOrEmpty(text)) return;

        inputField.text = "";
        StartCoroutine(dialogueClient.SendToNpc(npc, rangeDetector.CurrentDistance, text));
    }
}
