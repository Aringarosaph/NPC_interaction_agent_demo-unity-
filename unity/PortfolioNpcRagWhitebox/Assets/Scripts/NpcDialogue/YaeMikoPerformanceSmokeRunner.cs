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
        yield return new WaitForSeconds(0.3f);
        float idleTilt = GetBodyTilt(performance.animator);
        AnimatorStateInfo baseBefore = performance.animator.GetCurrentAnimatorStateInfo(0);

        performance.PlayPerformance("teasing", "nod", 0.5f);
        yield return new WaitForSeconds(0.3f);
        float gestureTilt = GetBodyTilt(performance.animator);
        AnimatorStateInfo baseAfter = performance.animator.GetCurrentAnimatorStateInfo(0);
        Debug.Log(
            $"YAE_RIG idle_tilt_deg={idleTilt:F3} gesture_tilt_deg={gestureTilt:F3} " +
            $"base_idle_progress={baseBefore.normalizedTime:F3}->{baseAfter.normalizedTime:F3}");

        if (idleTilt > 15f || gestureTilt > 15f)
        {
            complete(false, $"Yae Miko rig is tilted: idle={idleTilt:F2}, gesture={gestureTilt:F2} degrees.");
            yield break;
        }
        if (!baseBefore.IsName("idle") || !baseAfter.IsName("idle") || baseAfter.normalizedTime <= baseBefore.normalizedTime)
        {
            complete(false, "Full-body idle layer did not continue while the upper-body gesture played.");
            yield break;
        }

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

        AnimatorStateInfo state = performance.animator.GetCurrentAnimatorStateInfo(performance.actionLayerIndex);
        AnimatorStateInfo nextState = performance.animator.GetNextAnimatorStateInfo(performance.actionLayerIndex);
        if (!state.IsName("nod") && !nextState.IsName("nod"))
        {
            complete(false, $"Expected nod Animator state, current hash={state.shortNameHash}.");
            yield break;
        }
        performance.ResetPerformance();
        complete(true, "upright full-body idle, teasing BlendShapes, and upper-body nod played successfully.");
    }

    private static float GetBodyTilt(Animator animator)
    {
        Transform hips = animator.GetBoneTransform(HumanBodyBones.Hips);
        Transform head = animator.GetBoneTransform(HumanBodyBones.Head);
        return Vector3.Angle(head.position - hips.position, animator.transform.up);
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
