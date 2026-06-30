using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using TMPro;

public class PlayerChatInput : MonoBehaviour
{
    public TMP_InputField inputField;
    public Button sendButton;
    public DialogueRangeDetector rangeDetector;
    public NpcDialogueClient dialogueClient;
    public WhiteboxPlayerController playerController;
    public SimpleThirdPersonCamera followCamera;

    private bool isTyping;

    private void Start()
    {
        if (sendButton != null) sendButton.onClick.AddListener(Send);
        if (inputField != null) inputField.onSubmit.AddListener(_ => Send());
        SetTypingMode(false);
    }

    private void Update()
    {
        bool hasNpc = rangeDetector != null && rangeDetector.CurrentNpc != null;
        if (inputField != null)
        {
            inputField.interactable = hasNpc;
            if (!hasNpc && isTyping)
            {
                SetTypingMode(false);
            }
        }

        if (sendButton != null)
        {
            sendButton.interactable = hasNpc && inputField != null && !string.IsNullOrWhiteSpace(inputField.text);
        }

        if (hasNpc && !isTyping && Input.GetKeyDown(KeyCode.Return))
        {
            SetTypingMode(true);
        }
        else if (isTyping && Input.GetKeyDown(KeyCode.Escape))
        {
            SetTypingMode(false);
        }
    }

    public void Send()
    {
        if (rangeDetector == null || dialogueClient == null || inputField == null) return;
        var npc = rangeDetector.CurrentNpc;
        if (npc == null) return;
        if (!isTyping)
        {
            SetTypingMode(true);
            return;
        }

        string text = inputField.text.Trim();
        if (string.IsNullOrEmpty(text)) return;

        inputField.text = "";
        StartCoroutine(dialogueClient.SendToNpc(npc, rangeDetector.CurrentDistance, text));
        SetTypingMode(false);
    }

    private void SetTypingMode(bool enabled)
    {
        isTyping = enabled;

        if (playerController != null)
        {
            playerController.controlsEnabled = !enabled;
        }
        if (followCamera != null)
        {
            followCamera.SetLookEnabled(!enabled);
        }

        if (inputField == null) return;

        if (enabled)
        {
            inputField.Select();
            inputField.ActivateInputField();
            if (EventSystem.current != null)
            {
                EventSystem.current.SetSelectedGameObject(inputField.gameObject);
            }
        }
        else
        {
            inputField.DeactivateInputField();
            if (EventSystem.current != null && EventSystem.current.currentSelectedGameObject == inputField.gameObject)
            {
                EventSystem.current.SetSelectedGameObject(null);
            }
        }
    }
}
