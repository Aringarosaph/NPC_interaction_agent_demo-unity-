using System;
using System.Collections;
using UnityEngine;

public class YaeMikoPerformanceSmokeRunner : MonoBehaviour
{
    public IEnumerator Run(Action<bool, string> complete)
    {
        yield return null;

        NpcAgentMarker marker = FindYaeMiko();
        if (marker == null || marker.performanceController == null)
        {
            complete(false, "Yae Miko performance controller binding is missing.");
            yield break;
        }

        NpcPerformanceController performance = marker.performanceController;
        performance.ResetPerformance();
        performance.PlayPerformance("teasing", "nod", 0.5f);
        yield return new WaitForSeconds(0.3f);

        NpcPerformanceController.ExpressionPreset teasing = Array.Find(
            performance.expressionPresets,
            preset => preset != null && preset.id == "teasing");
        if (teasing == null || teasing.targets == null || teasing.targets.Length == 0)
        {
            complete(false, "Teasing expression preset is missing.");
            yield break;
        }

        foreach (NpcPerformanceController.BlendShapeTarget target in teasing.targets)
        {
            int index = performance.faceRenderer.sharedMesh.GetBlendShapeIndex(target.blendShapeName);
            float actual = index >= 0 ? performance.faceRenderer.GetBlendShapeWeight(index) : -1f;
            if (index < 0 || Mathf.Abs(actual - target.weight) > 2f)
            {
                complete(false, $"BlendShape {target.blendShapeName} expected {target.weight}, got {actual}.");
                yield break;
            }
        }

        AnimatorStateInfo state = performance.animator.GetCurrentAnimatorStateInfo(0);
        AnimatorStateInfo nextState = performance.animator.GetNextAnimatorStateInfo(0);
        if (!state.IsName("nod") && !nextState.IsName("nod"))
        {
            complete(false, $"Expected nod Animator state, current hash={state.shortNameHash}.");
            yield break;
        }

        performance.ResetPerformance();
        complete(true, "teasing BlendShapes and nod Humanoid animation played successfully.");
    }

    private static NpcAgentMarker FindYaeMiko()
    {
        foreach (NpcAgentMarker marker in UnityEngine.Object.FindObjectsByType<NpcAgentMarker>(FindObjectsInactive.Exclude))
        {
            if (marker != null && marker.npcId == "genshin_yae_miko") return marker;
        }
        return null;
    }
}
