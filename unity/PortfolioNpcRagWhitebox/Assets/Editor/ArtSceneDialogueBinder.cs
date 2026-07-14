using System.IO;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public static class ArtSceneDialogueBinder
{
    private const string ScenePath = "Assets/Scenes/Scene_PortfolioNpcRag.unity";
    private const string ChineseFontAssetPath = "Assets/Fonts/NotoSansCJKsc-Regular SDF.asset";
    private const string ColliderChildName = "NpcInteractionCapsule";

    private static readonly NpcBinding[] NpcBindings =
    {
        new NpcBinding("NPC_Amiya_Mesh", "arknights_amiya", "阿米娅"),
        new NpcBinding("NPC_YaeMiko_Mesh", "genshin_yae_miko", "八重神子"),
        new NpcBinding("NPC_Jinxi_Mesh", "wuwa_jinhsi", "今汐"),
    };

    [MenuItem("NPC Demo/Bind Art Scene Dialogue")]
    public static void BindArtSceneDialogue()
    {
        if (!File.Exists(ScenePath))
        {
            throw new FileNotFoundException($"Scene does not exist at {ScenePath}.");
        }

        Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        TMP_FontAsset font = RequireChineseFont();

        GameObject player = RequireObject("PlayerCapsule");
        GameObject canvasObject = RequireObject("Canvas");
        WhiteboxPlayerController playerController = RequireComponent<WhiteboxPlayerController>(player);
        SimpleThirdPersonCamera followCamera = RequireComponent<SimpleThirdPersonCamera>(RequireObject("Main Camera"));
        followCamera.minDistance = 2.2f;
        followCamera.maxDistance = 9f;
        followCamera.zoomSensitivity = 0.8f;
        followCamera.zoomSharpness = 12f;
        followCamera.firstPersonEyeHeight = 1.46f;
        followCamera.firstPersonForwardOffset = 0.18f;
        TMP_Text currentNpcLabel = RequireObject("CurrentNpcLabel").GetComponent<TMP_Text>();
        TMP_InputField inputField = RequireObject("ChatInput").GetComponent<TMP_InputField>();
        Button sendButton = RequireObject("SendButton").GetComponent<Button>();
        AgentDebugPanelController agentDebugPanel = EnsureAgentDebugPanel(canvasObject.transform, font, followCamera);

        DialogueRangeDetector rangeDetector = RequireComponent<DialogueRangeDetector>(RequireObject("DialogueSystem"));
        NpcDialogueClient dialogueClient = rangeDetector.GetComponent<NpcDialogueClient>();
        PlayerChatInput chatInput = rangeDetector.GetComponent<PlayerChatInput>();
        Require(dialogueClient != null, "DialogueSystem is missing NpcDialogueClient.");
        Require(chatInput != null, "DialogueSystem is missing PlayerChatInput.");

        rangeDetector.player = player.transform;
        rangeDetector.currentNpcLabel = currentNpcLabel;
        dialogueClient.endpoint = "http://127.0.0.1:8008/api/dialogue";
        dialogueClient.resetEndpoint = "http://127.0.0.1:8008/api/debug/reset";
        SpeechBubbleController playerBubble = FindPlayerBubble(player);
        ConfigureBubbleLayout(playerBubble);
        dialogueClient.playerBubble = playerBubble;
        dialogueClient.agentDebugPanel = agentDebugPanel;
        chatInput.inputField = inputField;
        chatInput.sendButton = sendButton;
        chatInput.rangeDetector = rangeDetector;
        chatInput.dialogueClient = dialogueClient;
        chatInput.playerController = playerController;
        chatInput.followCamera = followCamera;

        foreach (NpcBinding binding in NpcBindings)
        {
            BindNpc(binding, font);
        }

        EnsureEventSystem();
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        Debug.Log("Art scene dialogue bindings refreshed.");
    }

    private static void BindNpc(NpcBinding binding, TMP_FontAsset font)
    {
        GameObject npc = RequireObject(binding.objectName);
        NpcAgentMarker marker = EnsureComponent<NpcAgentMarker>(npc);
        marker.npcId = binding.npcId;
        marker.displayName = binding.displayName;
        marker.interactionRadius = 3f;
        marker.rangeCenter = npc.transform;

        Bounds bounds = CalculateRendererBounds(npc);
        EnsureInteractionCollider(npc);
        Transform bubbleAnchor = EnsureBubbleAnchor(npc.transform, bounds, font);
        EnsureNameplate(npc.transform, bounds, binding.displayName, font);
        marker.bubbleAnchor = bubbleAnchor;

        EditorUtility.SetDirty(npc);
        EditorUtility.SetDirty(marker);
    }

    private static void EnsureInteractionCollider(GameObject npc)
    {
        Transform child = npc.transform.Find(ColliderChildName);
        if (child == null)
        {
            child = new GameObject(ColliderChildName).transform;
            child.SetParent(npc.transform, false);
        }

        child.localPosition = Vector3.zero;
        child.localRotation = Quaternion.identity;
        SetWorldScale(child, Vector3.one);

        CapsuleCollider collider = child.GetComponent<CapsuleCollider>();
        if (collider == null)
        {
            collider = child.gameObject.AddComponent<CapsuleCollider>();
        }

        collider.center = new Vector3(0f, 1f, 0f);
        collider.height = 2f;
        collider.radius = 0.5f;
        collider.direction = 1;
        collider.isTrigger = false;
        EditorUtility.SetDirty(child.gameObject);
        EditorUtility.SetDirty(collider);
    }

    private static Transform EnsureBubbleAnchor(Transform parent, Bounds bounds, TMP_FontAsset font)
    {
        Transform anchor = parent.Find("BubbleAnchor");
        if (anchor == null)
        {
            anchor = new GameObject("BubbleAnchor").transform;
            anchor.SetParent(parent, false);
        }

        anchor.position = new Vector3(parent.position.x, bounds.max.y + 0.85f, parent.position.z);
        anchor.rotation = Quaternion.identity;
        SetWorldScale(anchor, Vector3.one);

        GameObject canvasObject = EnsureChild(anchor, "SpeechBubbleCanvas");
        canvasObject.transform.localPosition = Vector3.zero;
        canvasObject.transform.localRotation = Quaternion.identity;
        canvasObject.transform.localScale = Vector3.one * 0.01f;

        Canvas canvas = EnsureComponent<Canvas>(canvasObject);
        canvas.renderMode = RenderMode.WorldSpace;
        CanvasGroup group = EnsureComponent<CanvasGroup>(canvasObject);
        group.alpha = 0f;

        RectTransform canvasRect = EnsureRectTransform(canvasObject);
        canvasRect.sizeDelta = new Vector2(260f, 86f);
        canvasRect.pivot = new Vector2(0.5f, 0f);

        GameObject background = EnsureChild(canvasObject.transform, "BubbleBackground");
        RectTransform backgroundRect = EnsureRectTransform(background);
        backgroundRect.anchorMin = Vector2.zero;
        backgroundRect.anchorMax = Vector2.one;
        backgroundRect.offsetMin = Vector2.zero;
        backgroundRect.offsetMax = Vector2.zero;
        Image image = EnsureComponent<Image>(background);
        image.color = new Color(1f, 1f, 1f, 0.88f);

        GameObject textObject = EnsureChild(canvasObject.transform, "BubbleText");
        RectTransform textRect = EnsureRectTransform(textObject);
        textRect.anchorMin = Vector2.zero;
        textRect.anchorMax = Vector2.one;
        textRect.offsetMin = new Vector2(12f, 10f);
        textRect.offsetMax = new Vector2(-12f, -10f);
        TMP_Text text = EnsureComponent<TextMeshProUGUI>(textObject);
        text.font = font;
        text.text = string.Empty;
        text.fontSize = 24f;
        text.alignment = TextAlignmentOptions.Center;
        text.color = Color.black;
        text.textWrappingMode = TextWrappingModes.Normal;

        SpeechBubbleController bubble = EnsureComponent<SpeechBubbleController>(canvasObject);
        bubble.bubbleText = text;
        bubble.canvasGroup = group;
        bubble.bubbleRect = canvasRect;
        bubble.faceMainCamera = true;
        return anchor;
    }

    private static void EnsureNameplate(Transform parent, Bounds bounds, string displayName, TMP_FontAsset font)
    {
        GameObject plate = EnsureChild(parent, "Nameplate");
        plate.transform.position = new Vector3(parent.position.x, bounds.max.y + 0.25f, parent.position.z);
        plate.transform.rotation = Quaternion.identity;
        SetWorldScale(plate.transform, Vector3.one * 0.01f);

        Canvas canvas = EnsureComponent<Canvas>(plate);
        canvas.renderMode = RenderMode.WorldSpace;
        EnsureComponent<BillboardToCamera>(plate);
        RectTransform rect = EnsureRectTransform(plate);
        rect.sizeDelta = new Vector2(160f, 34f);

        GameObject background = EnsureChild(plate.transform, "NameplateBackground");
        RectTransform backgroundRect = EnsureRectTransform(background);
        backgroundRect.anchorMin = Vector2.zero;
        backgroundRect.anchorMax = Vector2.one;
        backgroundRect.offsetMin = Vector2.zero;
        backgroundRect.offsetMax = Vector2.zero;
        Image image = EnsureComponent<Image>(background);
        image.color = new Color(0f, 0f, 0f, 0.48f);

        GameObject textObject = EnsureChild(plate.transform, "NameplateText");
        RectTransform textRect = EnsureRectTransform(textObject);
        textRect.anchorMin = Vector2.zero;
        textRect.anchorMax = Vector2.one;
        textRect.offsetMin = new Vector2(8f, 2f);
        textRect.offsetMax = new Vector2(-8f, -2f);
        TMP_Text text = EnsureComponent<TextMeshProUGUI>(textObject);
        text.font = font;
        text.text = displayName;
        text.fontSize = 23f;
        text.alignment = TextAlignmentOptions.Center;
        text.color = Color.white;
    }

    private static SpeechBubbleController FindPlayerBubble(GameObject player)
    {
        Transform anchor = player.transform.Find("BubbleAnchor");
        if (anchor == null) return player.GetComponentInChildren<SpeechBubbleController>(true);
        return anchor.GetComponentInChildren<SpeechBubbleController>(true);
    }

    private static void ConfigureBubbleLayout(SpeechBubbleController bubble)
    {
        if (bubble == null) return;
        RectTransform rect = bubble.transform as RectTransform;
        if (rect == null) return;
        rect.pivot = new Vector2(0.5f, 0f);
        bubble.bubbleRect = rect;
        EditorUtility.SetDirty(rect);
        EditorUtility.SetDirty(bubble);
    }

    private static AgentDebugPanelController EnsureAgentDebugPanel(
        Transform parent,
        TMP_FontAsset font,
        SimpleThirdPersonCamera cameraController)
    {
        GameObject root = EnsureChild(parent, "AgentDebugPanel");
        RectTransform rect = EnsureRectTransform(root);
        rect.anchorMin = new Vector2(1f, 1f);
        rect.anchorMax = new Vector2(1f, 1f);
        rect.pivot = new Vector2(1f, 1f);
        rect.anchoredPosition = new Vector2(-18f, -18f);
        rect.sizeDelta = new Vector2(390f, 500f);
        Image image = EnsureComponent<Image>(root);
        image.color = new Color(0.04f, 0.05f, 0.06f, 0.82f);

        AgentDebugPanelController panel = EnsureComponent<AgentDebugPanelController>(root);
        panel.questStatusText = EnsurePanelText(root.transform, "QuestStatusText", "任务: 无", new Vector2(14f, -14f), new Vector2(252f, 54f), 16f, font);
        panel.resetButton = EnsurePanelButton(root.transform, "ResetDemoButton", "重置", new Vector2(-60f, -30f), new Vector2(92f, 32f), font);
        panel.viewToggleButton = EnsurePanelButton(root.transform, "ViewToggleButton", "切换视角", new Vector2(-170f, -30f), new Vector2(116f, 32f), font);
        panel.cameraController = cameraController;
        panel.relationshipText = EnsurePanelText(root.transform, "RelationshipText", "关系: 0 (neutral)", new Vector2(14f, -76f), new Vector2(362f, 24f), 16f, font);
        panel.inventoryText = EnsurePanelText(root.transform, "InventoryText", "背包: 无新增", new Vector2(14f, -108f), new Vector2(362f, 44f), 16f, font);
        panel.traceText = EnsurePanelText(root.transform, "AgentTraceText", "等待对话。", new Vector2(14f, -160f), new Vector2(362f, 326f), 14f, font);
        EditorUtility.SetDirty(root);
        EditorUtility.SetDirty(panel);
        return panel;
    }

    private static Button EnsurePanelButton(Transform parent, string name, string label, Vector2 position, Vector2 size, TMP_FontAsset font)
    {
        GameObject root = EnsureChild(parent, name);
        RectTransform rect = EnsureRectTransform(root);
        rect.anchorMin = new Vector2(1f, 1f);
        rect.anchorMax = new Vector2(1f, 1f);
        rect.pivot = new Vector2(0.5f, 0.5f);
        rect.anchoredPosition = position;
        rect.sizeDelta = size;

        Image image = EnsureComponent<Image>(root);
        image.color = new Color(0.18f, 0.42f, 0.86f, 0.95f);
        Button button = EnsureComponent<Button>(root);

        GameObject labelObject = EnsureChild(root.transform, "Label");
        RectTransform labelRect = EnsureRectTransform(labelObject);
        labelRect.anchorMin = Vector2.zero;
        labelRect.anchorMax = Vector2.one;
        labelRect.offsetMin = Vector2.zero;
        labelRect.offsetMax = Vector2.zero;
        TMP_Text text = EnsureComponent<TextMeshProUGUI>(labelObject);
        text.font = font;
        text.text = label;
        text.fontSize = 16f;
        text.alignment = TextAlignmentOptions.Center;
        text.color = Color.white;

        EditorUtility.SetDirty(root);
        EditorUtility.SetDirty(button);
        return button;
    }

    private static TMP_Text EnsurePanelText(Transform parent, string name, string value, Vector2 position, Vector2 size, float fontSize, TMP_FontAsset font)
    {
        GameObject textObject = EnsureChild(parent, name);
        RectTransform rect = EnsureRectTransform(textObject);
        rect.anchorMin = new Vector2(0f, 1f);
        rect.anchorMax = new Vector2(0f, 1f);
        rect.pivot = new Vector2(0f, 1f);
        rect.anchoredPosition = position;
        rect.sizeDelta = size;

        TMP_Text text = EnsureComponent<TextMeshProUGUI>(textObject);
        text.font = font;
        if (string.IsNullOrEmpty(text.text))
        {
            text.text = value;
        }
        text.fontSize = fontSize;
        text.alignment = TextAlignmentOptions.TopLeft;
        text.color = Color.white;
        text.textWrappingMode = TextWrappingModes.Normal;
        EditorUtility.SetDirty(textObject);
        EditorUtility.SetDirty(text);
        return text;
    }

    private static Bounds CalculateRendererBounds(GameObject obj)
    {
        Renderer[] renderers = obj.GetComponentsInChildren<Renderer>(true);
        bool hasBounds = false;
        Bounds bounds = new Bounds(obj.transform.position, Vector3.one * 2f);
        foreach (Renderer renderer in renderers)
        {
            if (renderer == null || renderer.GetComponentInParent<Canvas>() != null) continue;
            if (!hasBounds)
            {
                bounds = renderer.bounds;
                hasBounds = true;
            }
            else
            {
                bounds.Encapsulate(renderer.bounds);
            }
        }
        return bounds;
    }

    private static TMP_FontAsset RequireChineseFont()
    {
        TMP_FontAsset font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(ChineseFontAssetPath);
        Require(font != null, $"Chinese TMP font asset was not found at {ChineseFontAssetPath}.");
        return font;
    }

    private static GameObject EnsureChild(Transform parent, string childName)
    {
        Transform child = parent.Find(childName);
        if (child != null) return child.gameObject;

        GameObject obj = new GameObject(childName);
        obj.transform.SetParent(parent, false);
        return obj;
    }

    private static RectTransform EnsureRectTransform(GameObject obj)
    {
        RectTransform rect = obj.GetComponent<RectTransform>();
        if (rect == null)
        {
            rect = obj.AddComponent<RectTransform>();
        }
        return rect;
    }

    private static T EnsureComponent<T>(GameObject obj) where T : Component
    {
        T component = obj.GetComponent<T>();
        if (component == null)
        {
            component = obj.AddComponent<T>();
        }
        EditorUtility.SetDirty(component);
        return component;
    }

    private static T RequireComponent<T>(GameObject obj) where T : Component
    {
        T component = obj.GetComponent<T>();
        Require(component != null, $"{obj.name} is missing component {typeof(T).Name}.");
        return component;
    }

    private static GameObject RequireObject(string objectName)
    {
        GameObject obj = GameObject.Find(objectName);
        Require(obj != null, $"Scene object '{objectName}' was not found.");
        return obj;
    }

    private static void EnsureEventSystem()
    {
        if (Object.FindFirstObjectByType<EventSystem>() != null) return;
        GameObject eventSystem = new GameObject("EventSystem");
        eventSystem.AddComponent<EventSystem>();
        eventSystem.AddComponent<StandaloneInputModule>();
    }

    private static void SetWorldScale(Transform transform, Vector3 worldScale)
    {
        Transform parent = transform.parent;
        if (parent == null)
        {
            transform.localScale = worldScale;
            return;
        }

        Vector3 parentScale = parent.lossyScale;
        transform.localScale = new Vector3(
            SafeDivide(worldScale.x, parentScale.x),
            SafeDivide(worldScale.y, parentScale.y),
            SafeDivide(worldScale.z, parentScale.z));
    }

    private static float SafeDivide(float value, float divisor)
    {
        return Mathf.Abs(divisor) < 0.0001f ? value : value / divisor;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new System.InvalidOperationException(message);
        }
    }

    private readonly struct NpcBinding
    {
        public readonly string objectName;
        public readonly string npcId;
        public readonly string displayName;

        public NpcBinding(string objectName, string npcId, string displayName)
        {
            this.objectName = objectName;
            this.npcId = npcId;
            this.displayName = displayName;
        }
    }
}
