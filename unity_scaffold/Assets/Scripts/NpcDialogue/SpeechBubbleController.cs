using System.Collections;
using TMPro;
using UnityEngine;

public class SpeechBubbleController : MonoBehaviour
{
    public TMP_Text bubbleText;
    public CanvasGroup canvasGroup;
    public float defaultSeconds = 2.2f;

    private Coroutine current;

    public void Show(string text, float seconds = -1f)
    {
        if (current != null) StopCoroutine(current);
        current = StartCoroutine(ShowRoutine(text, seconds > 0 ? seconds : defaultSeconds));
    }

    private IEnumerator ShowRoutine(string text, float seconds)
    {
        bubbleText.text = text;
        if (canvasGroup != null) canvasGroup.alpha = 1f;
        yield return new WaitForSeconds(seconds);
        if (canvasGroup != null) canvasGroup.alpha = 0f;
        current = null;
    }
}
