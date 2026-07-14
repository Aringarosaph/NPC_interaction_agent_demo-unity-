using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class NpcPerformanceController : MonoBehaviour
{
    [Serializable]
    public class BlendShapeTarget
    {
        public string blendShapeName;
        [Range(0f, 100f)] public float weight;

        public BlendShapeTarget(string blendShapeName, float weight)
        {
            this.blendShapeName = blendShapeName;
            this.weight = weight;
        }
    }

    [Serializable]
    public class ExpressionPreset
    {
        public string id;
        public BlendShapeTarget[] targets;

        public ExpressionPreset(string id, params BlendShapeTarget[] targets)
        {
            this.id = id;
            this.targets = targets;
        }
    }

    [Serializable]
    public class ActionPreset
    {
        public string id;
        public string stateName;
        [Min(0f)] public float duration;

        public ActionPreset(string id, string stateName, float duration)
        {
            this.id = id;
            this.stateName = stateName;
            this.duration = duration;
        }
    }

    public SkinnedMeshRenderer faceRenderer;
    public Animator animator;
    public ExpressionPreset[] expressionPresets;
    public ActionPreset[] actionPresets;
    [Min(0)] public int actionLayerIndex;

    [Header("Transitions")]
    [Min(0f)] public float expressionBlendSeconds = 0.2f;
    [Min(0f)] public float actionCrossFadeSeconds = 0.15f;

    [Header("Automatic blink")]
    public bool enableBlink = true;
    public string blinkBlendShapeName = "まばたき";
    [Min(0.1f)] public float blinkIntervalMin = 2.5f;
    [Min(0.1f)] public float blinkIntervalMax = 5.5f;
    [Min(0.02f)] public float blinkCloseSeconds = 0.08f;
    [Min(0.02f)] public float blinkOpenSeconds = 0.11f;

    private readonly Dictionary<string, ExpressionPreset> expressions = new Dictionary<string, ExpressionPreset>(StringComparer.Ordinal);
    private readonly Dictionary<string, ActionPreset> actions = new Dictionary<string, ActionPreset>(StringComparer.Ordinal);
    private readonly Dictionary<string, int> blendShapeIndices = new Dictionary<string, int>(StringComparer.Ordinal);
    private readonly List<string> controlledBlendShapes = new List<string>();
    private Coroutine expressionRoutine;
    private Coroutine actionRoutine;
    private Coroutine blinkRoutine;
    private int blinkIndex = -1;
    private bool initialized;

    private void Awake()
    {
        Initialize();
        SetExpressionImmediate("neutral");
        PlayActionImmediate("idle");
    }

    private void OnEnable()
    {
        Initialize();
        if (enableBlink && blinkRoutine == null)
        {
            blinkRoutine = StartCoroutine(BlinkLoop());
        }
    }

    private void OnDisable()
    {
        if (blinkIndex >= 0 && faceRenderer != null)
        {
            faceRenderer.SetBlendShapeWeight(blinkIndex, 0f);
        }
        blinkRoutine = null;
    }

    public void PlayPerformance(string expressionId, string actionId, float holdSeconds)
    {
        Initialize();
        string safeExpression = expressions.ContainsKey(expressionId ?? string.Empty) ? expressionId : "neutral";
        string safeAction = actions.ContainsKey(actionId ?? string.Empty) ? actionId : "idle";

        if (expressionRoutine != null) StopCoroutine(expressionRoutine);
        expressionRoutine = StartCoroutine(ExpressionSequence(safeExpression, Mathf.Max(0f, holdSeconds)));

        if (actionRoutine != null) StopCoroutine(actionRoutine);
        actionRoutine = StartCoroutine(ActionSequence(safeAction));
    }

    public void ResetPerformance()
    {
        if (expressionRoutine != null) StopCoroutine(expressionRoutine);
        if (actionRoutine != null) StopCoroutine(actionRoutine);
        expressionRoutine = null;
        actionRoutine = null;
        SetExpressionImmediate("neutral");
        PlayActionImmediate("idle");
    }

    private void Initialize()
    {
        if (initialized) return;
        initialized = true;

        expressions.Clear();
        actions.Clear();
        blendShapeIndices.Clear();
        controlledBlendShapes.Clear();

        if (expressionPresets != null)
        {
            foreach (ExpressionPreset preset in expressionPresets)
            {
                if (preset == null || string.IsNullOrEmpty(preset.id)) continue;
                expressions[preset.id] = preset;
                if (preset.targets == null) continue;
                foreach (BlendShapeTarget target in preset.targets)
                {
                    if (target == null || string.IsNullOrEmpty(target.blendShapeName)) continue;
                    if (!controlledBlendShapes.Contains(target.blendShapeName))
                    {
                        controlledBlendShapes.Add(target.blendShapeName);
                    }
                }
            }
        }

        if (!expressions.ContainsKey("neutral"))
        {
            expressions["neutral"] = new ExpressionPreset("neutral");
        }

        if (actionPresets != null)
        {
            foreach (ActionPreset preset in actionPresets)
            {
                if (preset == null || string.IsNullOrEmpty(preset.id)) continue;
                actions[preset.id] = preset;
            }
        }

        if (faceRenderer != null && faceRenderer.sharedMesh != null)
        {
            foreach (string blendShapeName in controlledBlendShapes)
            {
                blendShapeIndices[blendShapeName] = faceRenderer.sharedMesh.GetBlendShapeIndex(blendShapeName);
            }
            blinkIndex = faceRenderer.sharedMesh.GetBlendShapeIndex(blinkBlendShapeName);
        }

        if (animator != null)
        {
            animator.applyRootMotion = false;
            animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        }
    }

    private IEnumerator ExpressionSequence(string expressionId, float holdSeconds)
    {
        yield return BlendToExpression(expressionId, expressionBlendSeconds);
        if (holdSeconds > 0f) yield return new WaitForSeconds(holdSeconds);
        yield return BlendToExpression("neutral", expressionBlendSeconds);
        expressionRoutine = null;
    }

    private IEnumerator BlendToExpression(string expressionId, float duration)
    {
        if (faceRenderer == null || !expressions.TryGetValue(expressionId, out ExpressionPreset preset)) yield break;

        var targetWeights = new Dictionary<string, float>(StringComparer.Ordinal);
        if (preset.targets != null)
        {
            foreach (BlendShapeTarget target in preset.targets)
            {
                if (target != null) targetWeights[target.blendShapeName] = target.weight;
            }
        }

        var startWeights = new Dictionary<string, float>(StringComparer.Ordinal);
        foreach (string blendShapeName in controlledBlendShapes)
        {
            if (TryGetBlendShapeIndex(blendShapeName, out int index))
            {
                startWeights[blendShapeName] = faceRenderer.GetBlendShapeWeight(index);
            }
        }

        if (duration <= 0f)
        {
            ApplyExpressionWeights(targetWeights, 1f, startWeights);
            yield break;
        }

        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            ApplyExpressionWeights(targetWeights, Mathf.Clamp01(elapsed / duration), startWeights);
            yield return null;
        }
        ApplyExpressionWeights(targetWeights, 1f, startWeights);
    }

    private void ApplyExpressionWeights(Dictionary<string, float> targets, float t, Dictionary<string, float> starts)
    {
        foreach (string blendShapeName in controlledBlendShapes)
        {
            if (!TryGetBlendShapeIndex(blendShapeName, out int index)) continue;
            float start = starts.TryGetValue(blendShapeName, out float startWeight) ? startWeight : 0f;
            float target = targets.TryGetValue(blendShapeName, out float targetWeight) ? targetWeight : 0f;
            faceRenderer.SetBlendShapeWeight(index, Mathf.Lerp(start, target, t));
        }
    }

    private void SetExpressionImmediate(string expressionId)
    {
        if (faceRenderer == null || !expressions.TryGetValue(expressionId, out ExpressionPreset preset)) return;
        foreach (string blendShapeName in controlledBlendShapes)
        {
            if (TryGetBlendShapeIndex(blendShapeName, out int index)) faceRenderer.SetBlendShapeWeight(index, 0f);
        }
        if (preset.targets == null) return;
        foreach (BlendShapeTarget target in preset.targets)
        {
            if (target != null && TryGetBlendShapeIndex(target.blendShapeName, out int index))
            {
                faceRenderer.SetBlendShapeWeight(index, target.weight);
            }
        }
    }

    private IEnumerator ActionSequence(string actionId)
    {
        if (!actions.TryGetValue(actionId, out ActionPreset action)) yield break;
        PlayActionImmediate(actionId);
        if (actionId != "idle" && action.duration > 0f)
        {
            yield return new WaitForSeconds(action.duration);
            PlayActionImmediate("idle");
        }
        actionRoutine = null;
    }

    private void PlayActionImmediate(string actionId)
    {
        if (animator == null || !actions.TryGetValue(actionId, out ActionPreset action)) return;
        int stateHash = Animator.StringToHash(action.stateName);
        if (actionLayerIndex < 0 || actionLayerIndex >= animator.layerCount) return;
        if (!animator.HasState(actionLayerIndex, stateHash)) return;
        animator.CrossFadeInFixedTime(stateHash, actionCrossFadeSeconds, actionLayerIndex);
    }

    private IEnumerator BlinkLoop()
    {
        while (enabled)
        {
            float min = Mathf.Min(blinkIntervalMin, blinkIntervalMax);
            float max = Mathf.Max(blinkIntervalMin, blinkIntervalMax);
            yield return new WaitForSeconds(UnityEngine.Random.Range(min, max));
            if (blinkIndex < 0 || faceRenderer == null) continue;
            yield return AnimateBlink(0f, 100f, blinkCloseSeconds);
            yield return AnimateBlink(100f, 0f, blinkOpenSeconds);
        }
    }

    private IEnumerator AnimateBlink(float from, float to, float duration)
    {
        float elapsed = 0f;
        while (elapsed < duration)
        {
            elapsed += Time.deltaTime;
            faceRenderer.SetBlendShapeWeight(blinkIndex, Mathf.Lerp(from, to, Mathf.Clamp01(elapsed / duration)));
            yield return null;
        }
        faceRenderer.SetBlendShapeWeight(blinkIndex, to);
    }

    private bool TryGetBlendShapeIndex(string blendShapeName, out int index)
    {
        return blendShapeIndices.TryGetValue(blendShapeName, out index) && index >= 0;
    }
}
