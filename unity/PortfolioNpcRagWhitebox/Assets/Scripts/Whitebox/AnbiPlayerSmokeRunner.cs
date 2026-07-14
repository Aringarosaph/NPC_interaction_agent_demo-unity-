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

        LogRigState("Idle", player.transform, visual, animator);
        CaptureMainCamera("/tmp/anbi_player_idle.png");
        if (!FeetAreGrounded(player.transform, visual))
        {
            complete(false, "Anbi's rendered feet are not aligned with the player ground point in Idle.");
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

        Quaternion[] idleLegs = GetLegRotations(visual);
        Transform weaponBone = FindDescendant(visual, "Anbi_Weapon_01");
        if (weaponBone == null)
        {
            complete(false, "Anbi weapon bone binding is missing.");
            yield break;
        }
        Quaternion idleWeaponRotation = weaponBone.localRotation;
        Vector3 idleWeaponPosition = weaponBone.localPosition;
        animator.SetFloat(MoveSpeedId, 1f);
        yield return new WaitForSeconds(0.3f);
        if (!IsState(animator, "Walk"))
        {
            complete(false, $"Expected Walk after startup completed, got {CurrentState(animator)}.");
            yield break;
        }

        LogRigState("Walk", player.transform, visual, animator);

        float legDelta = GetLargestLegDelta(visual, idleLegs);
        if (legDelta < 2f)
        {
            complete(false, $"Walk did not visibly animate the legs; max delta={legDelta:F2} degrees.");
            yield break;
        }
        float weaponDelta = Quaternion.Angle(idleWeaponRotation, weaponBone.localRotation) +
                            Vector3.Distance(idleWeaponPosition, weaponBone.localPosition) * 100f;
        if (weaponDelta < 0.05f)
        {
            complete(false, "Walk did not animate the bound weapon bone.");
            yield break;
        }
        if (!FeetAreGrounded(player.transform, visual, 0.2f))
        {
            complete(false, "Anbi's rendered feet are not aligned with the player ground point in Walk.");
            yield break;
        }

        CaptureMainCamera("/tmp/anbi_player_smoke.png");
        animator.SetFloat(MoveSpeedId, 0f);
        yield return null;
        if (!IsState(animator, "Idle"))
        {
            complete(false, $"Expected an Idle transition on the first frame after movement stopped, got {CurrentState(animator)}.");
            yield break;
        }
        yield return new WaitForSeconds(0.2f);
        if (!animator.GetCurrentAnimatorStateInfo(0).IsName("Idle"))
        {
            complete(false, $"Expected the Walk-to-Idle crossfade to complete, got {CurrentState(animator)}.");
            yield break;
        }

        AgentDebugPanelController debugPanel = UnityEngine.Object.FindFirstObjectByType<AgentDebugPanelController>();
        SimpleThirdPersonCamera followCamera = Camera.main != null
            ? Camera.main.GetComponent<SimpleThirdPersonCamera>()
            : null;
        if (debugPanel == null || debugPanel.viewToggleButton == null || followCamera == null ||
            debugPanel.cameraController != followCamera)
        {
            complete(false, "Camera view toggle UI binding is missing.");
            yield break;
        }

        debugPanel.viewToggleButton.onClick.Invoke();
        yield return null;
        Vector3 expectedFirstPersonPosition = player.transform.position +
                                              Vector3.up * followCamera.firstPersonEyeHeight +
                                              player.transform.forward * followCamera.firstPersonForwardOffset;
        if (!followCamera.IsFirstPerson || Vector3.Distance(followCamera.transform.position, expectedFirstPersonPosition) > 0.03f)
        {
            complete(false, "First-person camera did not switch to the stable player-root eye anchor.");
            yield break;
        }
        CaptureMainCamera("/tmp/anbi_first_person.png");

        debugPanel.viewToggleButton.onClick.Invoke();
        float oldDistance = followCamera.ThirdPersonDistance;
        followCamera.ApplyZoomInput(1f);
        if (followCamera.IsFirstPerson || followCamera.ThirdPersonDistance >= oldDistance)
        {
            complete(false, "Third-person camera did not restore or accept zoom input.");
            yield break;
        }

        complete(true, $"Idle/Walk, grounded feet, weapon bones, first-person toggle, and third-person zoom passed.");
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
        if (state.IsName("Walk")) return "Walk";
        return $"hash:{state.shortNameHash}";
    }

    private static Quaternion[] GetLegRotations(Transform visual)
    {
        Transform leftUpper = FindDescendant(visual, "Bip001 L Thigh");
        Transform leftLower = FindDescendant(visual, "Bip001 L Calf");
        Transform rightUpper = FindDescendant(visual, "Bip001 R Thigh");
        Transform rightLower = FindDescendant(visual, "Bip001 R Calf");
        if (leftUpper == null || leftLower == null || rightUpper == null || rightLower == null)
        {
            return Array.Empty<Quaternion>();
        }
        return new[] { leftUpper.localRotation, leftLower.localRotation, rightUpper.localRotation, rightLower.localRotation };
    }

    private static float GetLargestLegDelta(Transform visual, Quaternion[] reference)
    {
        Quaternion[] current = GetLegRotations(visual);
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

    private static void LogRigState(string state, Transform player, Transform visual, Animator animator)
    {
        Renderer[] renderers = visual.GetComponentsInChildren<Renderer>(true);
        Bounds bounds = renderers[0].bounds;
        foreach (Renderer renderer in renderers.Skip(1)) bounds.Encapsulate(renderer.bounds);
        Transform leftFoot = FindDescendant(visual, "Bip001 L Foot");
        Transform rightFoot = FindDescendant(visual, "Bip001 R Foot");
        Transform hips = FindDescendant(visual, "Bip001 Pelvis");
        Transform weapon = FindDescendant(visual, "Anbi_Weapon_01");
        Debug.Log(
            $"ANBI_RIG state={state} ground={player.position.y:F3} bounds_min={bounds.min.y:F3} " +
            $"left_foot={(leftFoot != null ? leftFoot.position.y : -1f):F3} " +
            $"right_foot={(rightFoot != null ? rightFoot.position.y : -1f):F3} " +
            $"hips={(hips != null ? hips.position.y : -1f):F3} " +
            $"weapon={(weapon != null ? weapon.position.ToString("F3") : "missing")}");
    }

    private static bool FeetAreGrounded(Transform player, Transform visual, float tolerance = 0.12f)
    {
        Renderer[] renderers = visual.GetComponentsInChildren<Renderer>(true);
        Bounds bounds = renderers[0].bounds;
        foreach (Renderer renderer in renderers.Skip(1)) bounds.Encapsulate(renderer.bounds);
        return Mathf.Abs(bounds.min.y - player.position.y) <= tolerance;
    }

    private static Transform FindDescendant(Transform root, string name)
    {
        foreach (Transform child in root.GetComponentsInChildren<Transform>(true))
        {
            if (child.name == name) return child;
        }
        return null;
    }
}
