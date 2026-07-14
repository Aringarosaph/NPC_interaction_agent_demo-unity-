using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class AnbiPlayerSetup
{
    private const string ScenePath = "Assets/Scenes/Scene_PortfolioNpcRag.unity";
    private const string ModelPath = "Assets/Mesh/Characters/Anbi/Anbi_TPose.FBX";
    private const string TextureFolder = "Assets/Mesh/Characters/Anbi/Textures";
    private const string AnimationFolder = "Assets/Animations/Anbi";
    private const string ControllerPath = AnimationFolder + "/AnbiLocomotion.controller";
    private const string PlayerName = "PlayerCapsule";
    private const string VisualName = "AnbiVisual";
    private const float TargetHeight = 1.56f;

    private static readonly ClipDefinition[] Clips =
    {
        new ClipDefinition("Idle", AnimationFolder + "/Anbi_Idle.FBX", true),
        new ClipDefinition("Walk", AnimationFolder + "/Anbi_Walk.FBX", true),
    };

    [MenuItem("NPC Demo/Configure Anbi Player")]
    public static void Configure()
    {
        Require(File.Exists(ModelPath), $"Missing Anbi model: {ModelPath}");
        foreach (ClipDefinition definition in Clips)
        {
            Require(File.Exists(definition.path), $"Missing Anbi animation: {definition.path}");
        }

        Avatar avatar = ConfigureModelImporter();
        AnimationClip[] clips = Clips.Select(definition => ConfigureAnimationImporter(definition, avatar)).ToArray();
        AnimatorController controller = BuildController(clips);
        ConfigureScene(avatar, controller);
        AssetDatabase.SaveAssets();
        Validate();
        Debug.Log("Anbi player model and locomotion configured.");
    }

    [MenuItem("NPC Demo/Validate Anbi Player")]
    public static void Validate()
    {
        Avatar avatar = LoadAvatar(ModelPath);
        Require(avatar != null && avatar.isValid && !avatar.isHuman, "Anbi model needs a valid Generic Avatar.");

        AnimatorController controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
        Require(controller != null, "Anbi locomotion controller is missing.");
        Require(controller.parameters.Any(parameter => parameter.name == "MoveSpeed"), "MoveSpeed parameter is missing.");

        foreach (ClipDefinition definition in Clips)
        {
            AnimationClip clip = LoadClip(definition.path, definition.name);
            Require(clip != null, $"Animation clip {definition.name} is missing.");
            Require(clip.isLooping == definition.loop, $"Animation loop setting is wrong for {definition.name}.");
            Require(
                AnimationUtility.GetCurveBindings(clip).Any(binding => IsWeaponPath(binding.path)),
                $"Animation clip {definition.name} is missing weapon-bone curves.");
        }

        Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        GameObject player = GameObject.Find(PlayerName);
        Require(player != null, $"Scene object {PlayerName} was not found.");
        Transform visual = player.transform.Find(VisualName);
        Require(visual != null, "AnbiVisual is missing from the player.");
        Require(player.GetComponent<MeshRenderer>() == null, "The old capsule renderer is still enabled.");

        WhiteboxPlayerController playerController = player.GetComponent<WhiteboxPlayerController>();
        Animator animator = visual.GetComponentInChildren<Animator>(true);
        Require(playerController != null && playerController.characterAnimator == animator, "Player animator binding is missing.");
        Require(animator != null && animator.avatar == avatar, "Anbi Animator is not using the model Avatar.");
        Require(animator.runtimeAnimatorController == controller, "Anbi Animator Controller binding is missing.");

        Bounds bounds = CalculateRendererBounds(visual.gameObject);
        Require(bounds.size.y > 1.45f && bounds.size.y < 1.65f, $"Anbi visual height is unexpected: {bounds.size.y:F3}m.");
        Debug.Log($"Anbi player validation passed. Visual height: {bounds.size.y:F3}m.");
    }

    private static Avatar ConfigureModelImporter()
    {
        ModelImporter importer = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
        Require(importer != null, "Anbi model importer was not found.");
        importer.globalScale = 100f;
        importer.animationType = ModelImporterAnimationType.Generic;
        importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
        importer.importAnimation = false;
        importer.importBlendShapes = true;
        importer.importCameras = false;
        importer.importLights = false;
        importer.materialImportMode = ModelImporterMaterialImportMode.ImportStandard;
        importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
        importer.SaveAndReimport();

        Directory.CreateDirectory(TextureFolder);
        importer = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
        Require(importer != null && importer.ExtractTextures(TextureFolder), "Unity could not extract Anbi's embedded textures.");
        AssetDatabase.Refresh();
        importer = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
        Require(importer != null, "Anbi model importer was lost after texture extraction.");
        importer.SaveAndReimport();

        Avatar avatar = LoadAvatar(ModelPath);
        Require(avatar != null && avatar.isValid && !avatar.isHuman, "Unity could not create a valid Generic Avatar for Anbi.");
        return avatar;
    }

    private static AnimationClip ConfigureAnimationImporter(ClipDefinition definition, Avatar avatar)
    {
        ModelImporter importer = AssetImporter.GetAtPath(definition.path) as ModelImporter;
        Require(importer != null, $"Animation importer was not found: {definition.path}");
        importer.globalScale = 100f;
        importer.animationType = ModelImporterAnimationType.Generic;
        importer.avatarSetup = ModelImporterAvatarSetup.CopyFromOther;
        importer.sourceAvatar = avatar;
        importer.importAnimation = true;
        importer.importCameras = false;
        importer.importLights = false;
        importer.materialImportMode = ModelImporterMaterialImportMode.None;

        ModelImporterClipAnimation[] importedClips = importer.defaultClipAnimations;
        Require(importedClips.Length > 0, $"No animation take was found in {definition.path}.");
        ModelImporterClipAnimation clip = importedClips[0];
        clip.name = definition.name;
        clip.loopTime = definition.loop;
        clip.loopPose = definition.loop;
        clip.lockRootRotation = true;
        clip.lockRootHeightY = true;
        clip.lockRootPositionXZ = true;
        clip.keepOriginalOrientation = false;
        clip.keepOriginalPositionY = false;
        clip.keepOriginalPositionXZ = false;
        importer.clipAnimations = new[] { clip };
        importer.SaveAndReimport();

        AnimationClip result = LoadClip(definition.path, definition.name);
        Require(result != null, $"Configured clip {definition.name} could not be loaded.");
        return result;
    }

    private static AnimatorController BuildController(AnimationClip[] clips)
    {
        if (AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath) != null)
        {
            AssetDatabase.DeleteAsset(ControllerPath);
        }

        AnimatorController controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
        controller.AddParameter("MoveSpeed", AnimatorControllerParameterType.Float);
        AnimatorStateMachine stateMachine = controller.layers[0].stateMachine;
        AnimatorState idle = stateMachine.AddState("Idle");
        AnimatorState walk = stateMachine.AddState("Walk");
        idle.motion = clips[0];
        walk.motion = clips[1];
        stateMachine.defaultState = idle;

        ConfigureTransition(idle.AddTransition(walk), false, 0f, 0.16f, AnimatorConditionMode.Greater, 0.08f);
        ConfigureTransition(walk.AddTransition(idle), false, 0f, 0.16f, AnimatorConditionMode.Less, 0.08f);
        EditorUtility.SetDirty(controller);
        return controller;
    }

    private static void ConfigureTransition(
        AnimatorStateTransition transition,
        bool hasExitTime,
        float exitTime,
        float duration,
        AnimatorConditionMode conditionMode,
        float threshold)
    {
        transition.hasExitTime = hasExitTime;
        transition.exitTime = exitTime;
        transition.hasFixedDuration = true;
        transition.duration = duration;
        transition.AddCondition(conditionMode, threshold, "MoveSpeed");
    }

    private static void ConfigureScene(Avatar avatar, AnimatorController controller)
    {
        Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        GameObject player = GameObject.Find(PlayerName);
        Require(player != null, $"Scene object {PlayerName} was not found.");

        CharacterController characterController = player.GetComponent<CharacterController>();
        WhiteboxPlayerController playerController = player.GetComponent<WhiteboxPlayerController>();
        Require(characterController != null && playerController != null, "Player movement components are missing.");

        float oldScaleY = player.transform.lossyScale.y;
        float groundY = player.transform.position.y +
            (characterController.center.y - characterController.height * 0.5f) * oldScaleY;
        player.transform.localScale = Vector3.one;
        player.transform.position = new Vector3(player.transform.position.x, groundY, player.transform.position.z);
        characterController.center = new Vector3(0f, TargetHeight * 0.5f, 0f);
        characterController.height = TargetHeight;
        characterController.radius = 0.32f;

        MeshRenderer capsuleRenderer = player.GetComponent<MeshRenderer>();
        MeshFilter capsuleFilter = player.GetComponent<MeshFilter>();
        if (capsuleRenderer != null) UnityEngine.Object.DestroyImmediate(capsuleRenderer);
        if (capsuleFilter != null) UnityEngine.Object.DestroyImmediate(capsuleFilter);

        Transform existing = player.transform.Find(VisualName);
        if (existing != null) UnityEngine.Object.DestroyImmediate(existing.gameObject);
        GameObject modelPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        Require(modelPrefab != null, "Anbi model prefab could not be loaded.");
        GameObject visual = PrefabUtility.InstantiatePrefab(modelPrefab, scene) as GameObject;
        Require(visual != null, "Anbi model could not be instantiated.");
        visual.name = VisualName;
        visual.transform.SetParent(player.transform, false);
        visual.transform.localPosition = Vector3.zero;
        visual.transform.localRotation = Quaternion.identity;
        visual.transform.localScale = Vector3.one;

        Bounds bounds = CalculateRendererBounds(visual);
        Require(bounds.size.y > 0.001f, "Anbi renderer bounds are empty.");
        float visualScale = TargetHeight / bounds.size.y;
        visual.transform.localScale = Vector3.one * visualScale;
        bounds = CalculateRendererBounds(visual);
        visual.transform.position += Vector3.up * (groundY - bounds.min.y);

        Animator animator = visual.GetComponentInChildren<Animator>(true);
        if (animator == null) animator = visual.AddComponent<Animator>();
        animator.avatar = avatar;
        animator.runtimeAnimatorController = controller;
        animator.applyRootMotion = false;
        animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
        playerController.characterAnimator = animator;

        Transform bubbleAnchor = player.transform.Find("BubbleAnchor");
        if (bubbleAnchor != null) bubbleAnchor.localPosition = new Vector3(0f, TargetHeight + 0.4f, 0f);

        EditorUtility.SetDirty(player);
        EditorUtility.SetDirty(characterController);
        EditorUtility.SetDirty(playerController);
        EditorUtility.SetDirty(animator);
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
    }

    private static Bounds CalculateRendererBounds(GameObject root)
    {
        Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
        Require(renderers.Length > 0, $"{root.name} has no renderers.");
        Bounds bounds = renderers[0].bounds;
        foreach (Renderer renderer in renderers.Skip(1)) bounds.Encapsulate(renderer.bounds);
        return bounds;
    }

    private static Avatar LoadAvatar(string path)
    {
        return AssetDatabase.LoadAllAssetsAtPath(path).OfType<Avatar>().FirstOrDefault();
    }

    private static AnimationClip LoadClip(string path, string name)
    {
        return AssetDatabase.LoadAllAssetsAtPath(path)
            .OfType<AnimationClip>()
            .FirstOrDefault(clip => clip.name == name);
    }

    private static bool IsWeaponPath(string path)
    {
        return path.IndexOf("Anbi_Weapon", StringComparison.OrdinalIgnoreCase) >= 0 ||
               path.IndexOf("Weapon_Bone", StringComparison.OrdinalIgnoreCase) >= 0;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private readonly struct ClipDefinition
    {
        public readonly string name;
        public readonly string path;
        public readonly bool loop;

        public ClipDefinition(string name, string path, bool loop)
        {
            this.name = name;
            this.path = path;
            this.loop = loop;
        }
    }
}
