using System;
using System.Collections;
using System.IO;
using System.Linq;
using UnityEngine;

public class AnbiPlayerSmokeRunner : MonoBehaviour
{
    private static readonly int MoveSpeedId = Animator.StringToHash("MoveSpeed");

    public IEnumerator Run(Action<bool, string> complete)
    {
        yield return null;

        GameObject player = GameObject.Find("PlayerCapsule");
        Transform visual = player != null ? player.transform.Find("AnbiVisual") : null;
        WhiteboxPlayerController controller = player != null ? player.GetComponent<WhiteboxPlayerController>() : null;
        Animator animator = visual != null ? visual.GetComponentInChildren<Animator>(true) : null;
        if (player == null || visual == null || controller == null || animator == null)
        {
            complete(false, "Anbi player runtime bindings are missing.");
            yield break;
        }

        controller.enabled = false;
        yield return new WaitForSeconds(0.25f);
        if (!IsState(animator, "Idle"))
        {
            complete(false, $"Expected Idle, got {CurrentState(animator)}.");
            yield break;
        }

        int texturedMaterials = visual.GetComponentsInChildren<Renderer>(true)
            .SelectMany(renderer => renderer.sharedMaterials)
            .Where(material => material != null)
            .Count(material => material.mainTexture != null);
        if (texturedMaterials < 3)
        {
            complete(false, $"Embedded Anbi textures were not assigned; textured materials={texturedMaterials}.");
            yield break;
        }

        Quaternion[] idleLegs = GetLegRotations(animator);
        animator.SetFloat(MoveSpeedId, 1f);
        yield return new WaitForSeconds(0.2f);
        if (!IsState(animator, "WalkStart"))
        {
            complete(false, $"Expected WalkStart after movement began, got {CurrentState(animator)}.");
            yield break;
        }

        yield return new WaitForSeconds(1.2f);
        if (!IsState(animator, "Walk"))
        {
            complete(false, $"Expected Walk after startup completed, got {CurrentState(animator)}.");
            yield break;
        }

        float legDelta = GetLargestLegDelta(animator, idleLegs);
        if (legDelta < 2f)
        {
            complete(false, $"Walk did not visibly animate the legs; max delta={legDelta:F2} degrees.");
            yield break;
        }

        CaptureMainCamera("/tmp/anbi_player_smoke.png");
        animator.SetFloat(MoveSpeedId, 0f);
        yield return new WaitForSeconds(0.35f);
        if (!IsState(animator, "Idle"))
        {
            complete(false, $"Expected Idle after movement stopped, got {CurrentState(animator)}.");
            yield break;
        }

        complete(true, $"Idle, WalkStart, Walk, textured materials ({texturedMaterials}), and leg motion ({legDelta:F1} deg) passed.");
    }

    private static bool IsState(Animator animator, string stateName)
    {
        return animator.GetCurrentAnimatorStateInfo(0).IsName(stateName) ||
               animator.GetNextAnimatorStateInfo(0).IsName(stateName);
    }

    private static string CurrentState(Animator animator)
    {
        AnimatorStateInfo state = animator.GetCurrentAnimatorStateInfo(0);
        if (state.IsName("Idle")) return "Idle";
        if (state.IsName("WalkStart")) return "WalkStart";
        if (state.IsName("Walk")) return "Walk";
        return $"hash:{state.shortNameHash}";
    }

    private static Quaternion[] GetLegRotations(Animator animator)
    {
        Transform leftUpper = animator.GetBoneTransform(HumanBodyBones.LeftUpperLeg);
        Transform leftLower = animator.GetBoneTransform(HumanBodyBones.LeftLowerLeg);
        Transform rightUpper = animator.GetBoneTransform(HumanBodyBones.RightUpperLeg);
        Transform rightLower = animator.GetBoneTransform(HumanBodyBones.RightLowerLeg);
        if (leftUpper == null || leftLower == null || rightUpper == null || rightLower == null)
        {
            return Array.Empty<Quaternion>();
        }
        return new[] { leftUpper.localRotation, leftLower.localRotation, rightUpper.localRotation, rightLower.localRotation };
    }

    private static float GetLargestLegDelta(Animator animator, Quaternion[] reference)
    {
        Quaternion[] current = GetLegRotations(animator);
        if (reference.Length != current.Length || reference.Length == 0) return 0f;
        float largest = 0f;
        for (int index = 0; index < current.Length; index++)
        {
            largest = Mathf.Max(largest, Quaternion.Angle(reference[index], current[index]));
        }
        return largest;
    }

    private static void CaptureMainCamera(string path)
    {
        Camera camera = Camera.main;
        if (camera == null) return;
        RenderTexture renderTexture = new RenderTexture(1280, 720, 24);
        Texture2D texture = new Texture2D(1280, 720, TextureFormat.RGB24, false);
        RenderTexture previousActive = RenderTexture.active;
        RenderTexture previousTarget = camera.targetTexture;
        camera.targetTexture = renderTexture;
        RenderTexture.active = renderTexture;
        camera.Render();
        texture.ReadPixels(new Rect(0f, 0f, 1280f, 720f), 0, 0);
        texture.Apply();
        File.WriteAllBytes(path, texture.EncodeToPNG());
        camera.targetTexture = previousTarget;
        RenderTexture.active = previousActive;
        UnityEngine.Object.Destroy(renderTexture);
        UnityEngine.Object.Destroy(texture);
    }
}
