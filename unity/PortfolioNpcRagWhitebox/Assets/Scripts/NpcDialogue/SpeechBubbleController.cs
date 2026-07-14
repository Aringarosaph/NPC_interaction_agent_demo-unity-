using System.Collections;
using TMPro;
using UnityEngine;

public class SpeechBubbleController : MonoBehaviour
{
    public TMP_Text bubbleText;
    public CanvasGroup canvasGroup;
    public RectTransform bubbleRect;
    public float defaultSeconds = 2.2f;
    public bool faceMainCamera = true;
    [Min(1f)] public float minHeight = 54f;
    [Min(1f)] public float maxHeight = 180f;
    [Min(0f)] public float verticalPadding = 20f;

    private Coroutine current;

    private void Awake()
    {
        if (bubbleRect == null) bubbleRect = transform as RectTransform;
        if (canvasGroup != null) canvasGroup.alpha = 0f;
    }

    private void LateUpdate()
    {
        if (!faceMainCamera || Camera.main == null) return;
        transform.rotation = Quaternion.LookRotation(transform.position - Camera.main.transform.position, Vector3.up);
    }

    public void Show(string text, float seconds = -1f)
    {
        if (bubbleText == null) return;
        if (current != null) StopCoroutine(current);
        current = StartCoroutine(ShowRoutine(text, seconds > 0 ? seconds : defaultSeconds));
    }

    private IEnumerator ShowRoutine(string text, float seconds)
    {
        bubbleText.text = text;
        ResizeToText(text);
        if (canvasGroup != null) canvasGroup.alpha = 1f;
        yield return new WaitForSeconds(seconds);
        if (canvasGroup != null) canvasGroup.alpha = 0f;
        current = null;
    }

    private void ResizeToText(string text)
    {
        if (bubbleRect == null) bubbleRect = transform as RectTransform;
        if (bubbleRect == null) return;

        float textWidth = Mathf.Max(1f, bubbleRect.rect.width - 24f);
        float preferredHeight = bubbleText.GetPreferredValues(text, textWidth, 0f).y;
        Vector2 size = bubbleRect.sizeDelta;
        size.y = Mathf.Clamp(preferredHeight + verticalPadding, minHeight, Mathf.Max(minHeight, maxHeight));
        bubbleRect.sizeDelta = size;
        Canvas.ForceUpdateCanvases();
    }
}
