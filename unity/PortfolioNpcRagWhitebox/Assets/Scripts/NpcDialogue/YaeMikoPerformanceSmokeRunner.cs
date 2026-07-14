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
        float idleRoll = GetBodyRoll(performance.animator);
        Quaternion[] legReference = GetLegRotations(performance.animator);

        performance.PlayPerformance("teasing", "dismissive", 1.2f);
        yield return new WaitForSeconds(0.05f);
        performance.PlayPerformance("teasing", "nod", 1.2f);
        float actionRoll = 0f;
        float lowerBodyDelta = 0f;
        bool sawActionState = false;
        for (int sample = 0; sample < 10; sample++)
        {
            yield return new WaitForSeconds(0.1f);
            actionRoll = Mathf.Max(actionRoll, GetBodyRoll(performance.animator));
            lowerBodyDelta = Mathf.Max(lowerBodyDelta, GetLargestLegDelta(performance.animator, legReference));
            AnimatorStateInfo state = performance.animator.GetCurrentAnimatorStateInfo(performance.actionLayerIndex);
            AnimatorStateInfo nextState = performance.animator.GetNextAnimatorStateInfo(performance.actionLayerIndex);
            sawActionState |= state.IsName("dismissive") || nextState.IsName("dismissive");
        }
        Debug.Log(
            $"YAE_RIG idle_roll_deg={idleRoll:F3} action_roll_max_deg={actionRoll:F3} " +
            $"lower_body_delta_max_deg={lowerBodyDelta:F3} queued={performance.PendingActionCount}");

        if (idleRoll > 3f || actionRoll > 8f)
        {
            complete(false, $"Yae Miko rig rolls sideways: idle={idleRoll:F2}, action={actionRoll:F2} degrees.");
            yield break;
        }
        if (lowerBodyDelta < 0.25f)
        {
            complete(false, $"Full-body action did not animate the legs; max delta={lowerBodyDelta:F3} degrees.");
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

        if (!sawActionState)
        {
            complete(false, "Expected dismissive full-body Animator state.");
            yield break;
        }

        if (performance.ActiveActionId != "dismissive" || performance.PendingActionCount != 1)
        {
            complete(false, $"Action queue interrupted dismissive: active={performance.ActiveActionId}, queued={performance.PendingActionCount}.");
            yield break;
        }

        NpcPerformanceController.ActionPreset dismissive = Array.Find(
            performance.actionPresets,
            preset => preset != null && preset.id == "dismissive");
        yield return new WaitForSeconds(Mathf.Max(0.1f, dismissive.duration - 1.05f + 0.15f));
        if (performance.ActiveActionId != "nod")
        {
            complete(false, $"Queued nod did not start after dismissive completed; active={performance.ActiveActionId}.");
            yield break;
        }

        SpeechBubbleController bubble = marker.bubbleAnchor != null
            ? marker.bubbleAnchor.GetComponentInChildren<SpeechBubbleController>(true)
            : null;
        if (bubble == null || bubble.bubbleRect == null)
        {
            complete(false, "Yae Miko adaptive speech bubble binding is missing.");
            yield break;
        }
        bubble.Show("短句", 0.2f);
        yield return null;
        float shortHeight = bubble.bubbleRect.sizeDelta.y;
        bubble.Show("这是一句用来验证气泡高度会随着多行文字内容自动增长的测试台词。", 0.2f);
        yield return null;
        float longHeight = bubble.bubbleRect.sizeDelta.y;
        if (longHeight <= shortHeight)
        {
            complete(false, $"Speech bubble did not grow for wrapped text: short={shortHeight}, long={longHeight}.");
            yield break;
        }

        performance.ResetPerformance();
        complete(true, "weighted leg animation, queued crossfades, teasing BlendShapes, and adaptive bubble height passed.");
    }

    private static float GetBodyRoll(Animator animator)
    {
        Transform hips = animator.GetBoneTransform(HumanBodyBones.Hips);
        Transform head = animator.GetBoneTransform(HumanBodyBones.Head);
        Vector3 localAxis = animator.transform.InverseTransformDirection((head.position - hips.position).normalized);
        return Mathf.Abs(Mathf.Atan2(localAxis.x, localAxis.y) * Mathf.Rad2Deg);
    }

    private static Quaternion[] GetLegRotations(Animator animator)
    {
        return new[]
        {
            animator.GetBoneTransform(HumanBodyBones.LeftUpperLeg).localRotation,
            animator.GetBoneTransform(HumanBodyBones.LeftLowerLeg).localRotation,
            animator.GetBoneTransform(HumanBodyBones.RightUpperLeg).localRotation,
            animator.GetBoneTransform(HumanBodyBones.RightLowerLeg).localRotation,
        };
    }

    private static float GetLargestLegDelta(Animator animator, Quaternion[] reference)
    {
        Quaternion[] current = GetLegRotations(animator);
        float largest = 0f;
        for (int index = 0; index < current.Length; index++)
        {
            largest = Mathf.Max(largest, Quaternion.Angle(reference[index], current[index]));
        }
        return largest;
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
