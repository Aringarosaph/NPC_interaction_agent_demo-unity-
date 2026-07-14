using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class YaeMikoPerformanceSetup
{
    private const string ScenePath = "Assets/Scenes/Scene_PortfolioNpcRag.unity";
    private const string ModelPath = "Assets/Mesh/Characters/YaeMiko/八重神子.fbx";
    private const string AnimationFolder = "Assets/Animations/YaeMiko";
    private const string ControllerPath = AnimationFolder + "/YaeMikoPerformance.controller";
    private const string NpcObjectName = "NPC_YaeMiko_Mesh";

    private static readonly string[] ActionIds =
    {
        "idle", "nod", "soft_laugh", "thoughtful", "dismissive", "hand_on_chest",
    };

    private static readonly string[] RequiredBlendShapes =
    {
        "口角上げ", "ウィンク", "ウィンク右", "眼角下", "にやり", "笑い", "にやり 2",
        "眼角上", "口横狭め", "真面目左", "真面目右", "まばたき",
    };

    [MenuItem("NPC Demo/Configure Yae Miko Performance")]
    public static void Configure()
    {
        Avatar avatar = EnsureHumanoidAvatar();
        Dictionary<string, AnimationClip> clips = ConfigureAnimationImporters();
        AnimatorController animatorController = BuildAnimatorController(clips);

        ArtSceneDialogueBinder.BindArtSceneDialogue();
        Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        GameObject npc = GameObject.Find(NpcObjectName);
        Require(npc != null, $"Scene object {NpcObjectName} was not found.");

        SkinnedMeshRenderer faceRenderer = FindFaceRenderer(npc);
        Dictionary<string, string> names = ResolveBlendShapeNames(faceRenderer.sharedMesh);
        Animator animator = npc.GetComponentInChildren<Animator>(true);
        if (animator == null) animator = npc.AddComponent<Animator>();
        animator.avatar = avatar;
        animator.runtimeAnimatorController = animatorController;
        animator.applyRootMotion = false;
        animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;

        NpcPerformanceController performance = npc.GetComponent<NpcPerformanceController>();
        if (performance == null) performance = npc.AddComponent<NpcPerformanceController>();
        performance.faceRenderer = faceRenderer;
        performance.animator = animator;
        performance.expressionPresets = BuildExpressionPresets(names);
        performance.actionPresets = BuildActionPresets(clips);
        performance.actionLayerIndex = 0;
        performance.blinkBlendShapeName = names["まばたき"];
        performance.enableBlink = true;

        NpcAgentMarker marker = npc.GetComponent<NpcAgentMarker>();
        Require(marker != null, "Yae Miko is missing NpcAgentMarker after scene binding.");
        marker.performanceController = performance;

        EditorUtility.SetDirty(animator);
        EditorUtility.SetDirty(performance);
        EditorUtility.SetDirty(marker);
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        Validate();
        Debug.Log("Yae Miko performance assets and scene bindings configured.");
    }

    [MenuItem("NPC Demo/Validate Yae Miko Performance")]
    public static void Validate()
    {
        foreach (string actionId in ActionIds)
        {
            Require(File.Exists(GetAnimationPath(actionId)), $"Missing animation FBX: {actionId}.fbx");
        }

        AnimatorController animatorController = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
        Require(animatorController != null, "Yae Miko Animator Controller is missing.");
        Require(animatorController.layers.Length == 1, "Yae Miko Animator Controller should use one full-body layer.");

        Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        GameObject npc = GameObject.Find(NpcObjectName);
        Require(npc != null, $"Scene object {NpcObjectName} was not found.");
        NpcAgentMarker marker = npc.GetComponent<NpcAgentMarker>();
        NpcPerformanceController performance = npc.GetComponent<NpcPerformanceController>();
        Require(marker != null && marker.performanceController == performance, "NpcAgentMarker performance binding is missing.");
        Require(performance != null, "NpcPerformanceController is missing.");
        Require(performance.faceRenderer != null && performance.faceRenderer.sharedMesh != null, "Face renderer binding is missing.");
        Require(performance.animator != null && performance.animator.runtimeAnimatorController == animatorController, "Animator binding is missing.");

        Dictionary<string, string> names = ResolveBlendShapeNames(performance.faceRenderer.sharedMesh);
        Require(names.Count == RequiredBlendShapes.Length, "Not all required BlendShapes were resolved.");
        Require(performance.expressionPresets != null && performance.expressionPresets.Length == 6, "Expected six expression presets.");
        Require(performance.actionPresets != null && performance.actionPresets.Length == 6, "Expected six action presets.");

        foreach (string actionId in ActionIds)
        {
            Require(performance.actionPresets.Any(p => p.id == actionId), $"Action preset {actionId} is missing.");
            Require(performance.animator.HasState(performance.actionLayerIndex, Animator.StringToHash(actionId)), $"Animator state {actionId} is missing.");
        }
        Debug.Log("Yae Miko performance validation passed.");
    }

    private static Avatar RequireAvatar()
    {
        Avatar avatar = AssetDatabase.LoadAllAssetsAtPath(ModelPath).OfType<Avatar>().FirstOrDefault();
        Require(avatar != null && avatar.isValid && avatar.isHuman, "Yae Miko model does not contain a valid Humanoid Avatar.");
        return avatar;
    }

    private static Avatar EnsureHumanoidAvatar()
    {
        Avatar existing = AssetDatabase.LoadAllAssetsAtPath(ModelPath).OfType<Avatar>().FirstOrDefault();
        ModelImporter currentImporter = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
        if (existing != null && existing.isValid && existing.isHuman && HasExpectedHipMapping(currentImporter)) return existing;

        ModelImporter importer = currentImporter;
        Require(importer != null, "Yae Miko source model importer was not found.");
        importer.animationType = ModelImporterAnimationType.Human;
        importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
        importer.SaveAndReimport();

        importer = AssetImporter.GetAtPath(ModelPath) as ModelImporter;
        HumanDescription description = importer.humanDescription;
        HumanBone[] humanBones = BuildHumanoidBoneMap();
        SkeletonBone[] skeletonBones = BuildValidTPose(humanBones);
        description.human = humanBones;
        description.skeleton = skeletonBones;
        description.armStretch = 0.05f;
        description.legStretch = 0.05f;
        description.upperArmTwist = 0.5f;
        description.lowerArmTwist = 0.5f;
        description.upperLegTwist = 0.5f;
        description.lowerLegTwist = 0.5f;
        description.feetSpacing = 0f;
        description.hasTranslationDoF = false;
        importer.humanDescription = description;
        importer.SaveAndReimport();
        return RequireAvatar();
    }

    private static bool HasExpectedHipMapping(ModelImporter importer)
    {
        if (importer == null) return false;
        HumanDescription description = importer.humanDescription;
        HumanBone hips = description.human.FirstOrDefault(
            bone => bone.humanName == HumanTrait.BoneName[(int)HumanBodyBones.Hips]);
        SkeletonBone skeletonHips = description.skeleton.FirstOrDefault(bone => bone.name == "腰");
        float hipRoll = Mathf.Abs(Mathf.DeltaAngle(0f, skeletonHips.rotation.eulerAngles.z));
        return hips.boneName == "腰" && hipRoll < 0.1f;
    }

    private static HumanBone[] BuildHumanoidBoneMap()
    {
        return new[]
        {
            Bone(HumanBodyBones.Hips, "腰"),
            Bone(HumanBodyBones.Spine, "上半身"),
            Bone(HumanBodyBones.Chest, "上半身3"),
            Bone(HumanBodyBones.UpperChest, "上半身2"),
            Bone(HumanBodyBones.Neck, "首"),
            Bone(HumanBodyBones.Head, "頭"),
            Bone(HumanBodyBones.LeftShoulder, "肩.L"),
            Bone(HumanBodyBones.RightShoulder, "肩.R"),
            Bone(HumanBodyBones.LeftUpperArm, "腕.L"),
            Bone(HumanBodyBones.RightUpperArm, "腕.R"),
            Bone(HumanBodyBones.LeftLowerArm, "ひじ.L"),
            Bone(HumanBodyBones.RightLowerArm, "ひじ.R"),
            Bone(HumanBodyBones.LeftHand, "手首.L"),
            Bone(HumanBodyBones.RightHand, "手首.R"),
            Bone(HumanBodyBones.LeftUpperLeg, "足.L"),
            Bone(HumanBodyBones.RightUpperLeg, "足.R"),
            Bone(HumanBodyBones.LeftLowerLeg, "ひざ.L"),
            Bone(HumanBodyBones.RightLowerLeg, "ひざ.R"),
            Bone(HumanBodyBones.LeftFoot, "足首.L"),
            Bone(HumanBodyBones.RightFoot, "足首.R"),
            Bone(HumanBodyBones.LeftToes, "つま先.L"),
            Bone(HumanBodyBones.RightToes, "つま先.R"),
            Bone(HumanBodyBones.LeftEye, "目.L"),
            Bone(HumanBodyBones.RightEye, "目.R"),
        };
    }

    private static HumanBone Bone(HumanBodyBones humanBodyBone, string modelBoneName)
    {
        return new HumanBone
        {
            humanName = HumanTrait.BoneName[(int)humanBodyBone],
            boneName = modelBoneName,
            limit = new HumanLimit { useDefaultValues = true },
        };
    }

    private static SkeletonBone[] BuildValidTPose(HumanBone[] humanBones)
    {
        GameObject modelPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath);
        Require(modelPrefab != null, "Yae Miko model prefab could not be loaded for T-Pose setup.");

        Type setupTool = typeof(Editor).Assembly.GetType("UnityEditor.AvatarSetupTool");
        Require(setupTool != null, "Unity Avatar T-Pose setup API is unavailable.");
        BindingFlags flags = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
        MethodInfo sampleBindPose = setupTool.GetMethod("SampleBindPose", flags);
        MethodInfo getModelBones = setupTool.GetMethods(flags).Single(
            method => method.Name == "GetModelBones" && method.GetParameters().Length == 3);
        MethodInfo getHumanBones = setupTool.GetMethods(flags).Single(
            method => method.Name == "GetHumanBones" &&
                      method.GetParameters().Length == 2 &&
                      method.GetParameters()[0].ParameterType == typeof(Dictionary<string, string>));
        MethodInfo makePoseValid = setupTool.GetMethod("MakePoseValid", flags);
        MethodInfo getSkeletonBones = setupTool.GetMethod("GetSkeletonBones", flags);
        Require(sampleBindPose != null && makePoseValid != null && getSkeletonBones != null, "Unity Avatar pose methods are unavailable.");

        GameObject instance = UnityEngine.Object.Instantiate(modelPrefab);
        instance.hideFlags = HideFlags.HideAndDontSave;
        try
        {
            sampleBindPose.Invoke(null, new object[] { instance });
            object modelBones = getModelBones.Invoke(null, new object[] { instance.transform, true, null });
            var mappings = humanBones.ToDictionary(bone => bone.humanName, bone => bone.boneName, StringComparer.Ordinal);
            Array wrappers = getHumanBones.Invoke(null, new object[] { mappings, modelBones }) as Array;
            Require(wrappers != null && wrappers.Length > 0, "Unity could not map the Yae Miko Humanoid bones.");
            makePoseValid.Invoke(null, new object[] { wrappers });
            SkeletonBone[] result = getSkeletonBones.Invoke(null, new object[] { instance.transform }) as SkeletonBone[];
            Require(result != null && result.Length > 0, "Unity did not return a valid T-Pose skeleton.");
            NormalizeHipRoll(result);
            return result;
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }

    private static void NormalizeHipRoll(SkeletonBone[] skeletonBones)
    {
        int hipsIndex = Array.FindIndex(skeletonBones, bone => bone.name == "腰");
        Require(hipsIndex >= 0, "Yae Miko T-Pose skeleton is missing its Hips bone.");
        SkeletonBone hips = skeletonBones[hipsIndex];
        Vector3 euler = hips.rotation.eulerAngles;
        hips.rotation = Quaternion.Euler(euler.x, euler.y, 0f);
        skeletonBones[hipsIndex] = hips;
    }

    private static Dictionary<string, AnimationClip> ConfigureAnimationImporters()
    {
        var clips = new Dictionary<string, AnimationClip>(StringComparer.Ordinal);
        foreach (string actionId in ActionIds)
        {
            string path = GetAnimationPath(actionId);
            Require(File.Exists(path), $"Missing animation FBX: {path}");
            ModelImporter importer = AssetImporter.GetAtPath(path) as ModelImporter;
            Require(importer != null, $"Animation asset is not a model: {path}");

            Avatar importedAvatar = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Avatar>().FirstOrDefault();
            if (importedAvatar == null || !importedAvatar.isValid || !importedAvatar.isHuman)
            {
                importer.animationType = ModelImporterAnimationType.Generic;
                importer.avatarSetup = ModelImporterAvatarSetup.NoAvatar;
                importer.sourceAvatar = null;
                importer.importAnimation = true;
                importer.SaveAndReimport();

                importer = AssetImporter.GetAtPath(path) as ModelImporter;
                importer.animationType = ModelImporterAnimationType.Human;
                importer.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                importer.sourceAvatar = null;
                importer.importAnimation = true;
                importer.SaveAndReimport();
                importer = AssetImporter.GetAtPath(path) as ModelImporter;
            }

            ModelImporterClipAnimation[] clipSettings = importer.defaultClipAnimations;
            if (clipSettings == null || clipSettings.Length == 0) clipSettings = importer.clipAnimations;
            Require(clipSettings != null && clipSettings.Length > 0, $"Animation FBX has no clips: {path}");
            foreach (ModelImporterClipAnimation settings in clipSettings)
            {
                bool loop = actionId == "idle";
                settings.name = actionId;
                settings.loopTime = loop;
                settings.loopPose = loop;
                settings.lockRootRotation = true;
                settings.lockRootHeightY = true;
                settings.lockRootPositionXZ = true;
            }
            importer.clipAnimations = clipSettings;
            importer.SaveAndReimport();

            AnimationClip clip = AssetDatabase.LoadAllAssetsAtPath(path)
                .OfType<AnimationClip>()
                .FirstOrDefault(candidate => !candidate.name.StartsWith("__preview__", StringComparison.Ordinal));
            Require(clip != null, $"Imported animation clip was not found: {path}");
            clips[actionId] = clip;
        }
        return clips;
    }

    private static AnimatorController BuildAnimatorController(Dictionary<string, AnimationClip> clips)
    {
        AnimatorController controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
        if (controller == null)
        {
            controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
        }

        while (controller.layers.Length > 1) controller.RemoveLayer(controller.layers.Length - 1);
        AnimatorControllerLayer layer = controller.layers[0];
        layer.name = "Full Body Performance";
        layer.defaultWeight = 1f;
        layer.avatarMask = null;
        AnimatorStateMachine stateMachine = layer.stateMachine;
        foreach (ChildAnimatorState childState in stateMachine.states.ToArray())
        {
            stateMachine.RemoveState(childState.state);
        }

        for (int index = 0; index < ActionIds.Length; index++)
        {
            string actionId = ActionIds[index];
            AnimatorState state = stateMachine.AddState(actionId, new Vector3(240f, 40f + index * 55f));
            state.motion = clips[actionId];
            state.writeDefaultValues = true;
            if (actionId == "idle") stateMachine.defaultState = state;
        }
        controller.layers = new[] { layer };
        EditorUtility.SetDirty(controller);
        AssetDatabase.SaveAssets();
        return controller;
    }

    private static SkinnedMeshRenderer FindFaceRenderer(GameObject npc)
    {
        foreach (SkinnedMeshRenderer renderer in npc.GetComponentsInChildren<SkinnedMeshRenderer>(true))
        {
            if (renderer.sharedMesh == null) continue;
            bool containsAll = RequiredBlendShapes.All(name => ResolveBlendShapeName(renderer.sharedMesh, name) != null);
            if (containsAll) return renderer;
        }
        throw new InvalidOperationException("No SkinnedMeshRenderer contains all required Yae Miko BlendShapes.");
    }

    private static Dictionary<string, string> ResolveBlendShapeNames(Mesh mesh)
    {
        var names = new Dictionary<string, string>(StringComparer.Ordinal);
        foreach (string requiredName in RequiredBlendShapes)
        {
            string resolved = ResolveBlendShapeName(mesh, requiredName);
            Require(resolved != null, $"BlendShape {requiredName} was not found on mesh {mesh.name}.");
            names[requiredName] = resolved;
        }
        return names;
    }

    private static string ResolveBlendShapeName(Mesh mesh, string expected)
    {
        int exactIndex = mesh.GetBlendShapeIndex(expected);
        if (exactIndex >= 0) return mesh.GetBlendShapeName(exactIndex);
        for (int index = 0; index < mesh.blendShapeCount; index++)
        {
            string candidate = mesh.GetBlendShapeName(index);
            string suffix = candidate.Contains(".") ? candidate.Substring(candidate.LastIndexOf('.') + 1) : candidate;
            if (NormalizeBlendShapeName(suffix) == NormalizeBlendShapeName(expected)) return candidate;
        }
        return null;
    }

    private static string NormalizeBlendShapeName(string value)
    {
        return value.Replace(" ", string.Empty).Replace("２", "2");
    }

    private static NpcPerformanceController.ExpressionPreset[] BuildExpressionPresets(Dictionary<string, string> names)
    {
        NpcPerformanceController.BlendShapeTarget Shape(string name, float weight)
            => new NpcPerformanceController.BlendShapeTarget(names[name], weight);

        return new[]
        {
            new NpcPerformanceController.ExpressionPreset("neutral"),
            new NpcPerformanceController.ExpressionPreset("soft_smile",
                Shape("口角上げ", 100f), Shape("ウィンク", 25f), Shape("ウィンク右", 25f), Shape("眼角下", 25f)),
            new NpcPerformanceController.ExpressionPreset("amused",
                Shape("にやり", 60f), Shape("笑い", 100f)),
            new NpcPerformanceController.ExpressionPreset("teasing",
                Shape("にやり 2", 100f), Shape("笑い", 50f), Shape("眼角上", 25f)),
            new NpcPerformanceController.ExpressionPreset("concerned",
                Shape("口横狭め", 30f), Shape("真面目左", 25f), Shape("真面目右", 25f)),
            new NpcPerformanceController.ExpressionPreset("stern",
                Shape("口横狭め", 30f), Shape("真面目左", 50f), Shape("真面目右", 50f), Shape("眼角上", 30f)),
        };
    }

    private static NpcPerformanceController.ActionPreset[] BuildActionPresets(Dictionary<string, AnimationClip> clips)
    {
        return ActionIds.Select(actionId => new NpcPerformanceController.ActionPreset(
            actionId,
            actionId,
            actionId == "idle" ? 0f : clips[actionId].length
        )).ToArray();
    }

    private static string GetAnimationPath(string actionId) => $"{AnimationFolder}/{actionId}.fbx";

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }
}
