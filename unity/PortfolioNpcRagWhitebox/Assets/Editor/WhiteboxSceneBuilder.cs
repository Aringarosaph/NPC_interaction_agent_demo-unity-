using System.IO;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public static class WhiteboxSceneBuilder
{
    private const string ScenePath = "Assets/Scenes/Scene_PortfolioNpcRag.unity";

    [MenuItem("NPC Demo/Build Whitebox Scene")]
    public static void BuildWhiteboxScene()
    {
        Directory.CreateDirectory("Assets/Scenes");

        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        scene.name = "Scene_PortfolioNpcRag";

        Material playerMaterial = CreateMaterial("Whitebox_Player_Blue", new Color(0.25f, 0.5f, 1f));
        Material amiyaMaterial = CreateMaterial("Whitebox_Amiya_Teal", new Color(0.2f, 0.75f, 0.78f));
        Material yaeMaterial = CreateMaterial("Whitebox_Yae_Pink", new Color(0.92f, 0.35f, 0.64f));
        Material jinhsiMaterial = CreateMaterial("Whitebox_Jinhsi_Gold", new Color(0.95f, 0.72f, 0.25f));
        Material floorMaterial = CreateMaterial("Whitebox_Floor_Matte", new Color(0.55f, 0.58f, 0.58f));

        GameObject floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        floor.name = "Floor";
        floor.transform.position = new Vector3(0f, -0.05f, 3f);
        floor.transform.localScale = new Vector3(14f, 0.1f, 14f);
        floor.GetComponent<Renderer>().sharedMaterial = floorMaterial;

        GameObject player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        player.name = "PlayerCapsule";
        player.transform.position = new Vector3(0f, 1f, -3f);
        player.GetComponent<Renderer>().sharedMaterial = playerMaterial;
        Object.DestroyImmediate(player.GetComponent<CapsuleCollider>());
        CharacterController characterController = player.AddComponent<CharacterController>();
        characterController.center = Vector3.zero;
        characterController.height = 2f;
        characterController.radius = 0.45f;
        WhiteboxPlayerController playerController = player.AddComponent<WhiteboxPlayerController>();
        Transform playerBubbleAnchor = CreateBubbleAnchor(player.transform, "BubbleAnchor", new Vector3(0f, 2.35f, 0f));

        GameObject cameraObject = new GameObject("Main Camera");
        Camera camera = cameraObject.AddComponent<Camera>();
        camera.tag = "MainCamera";
        camera.fieldOfView = 55f;
        SimpleThirdPersonCamera followCamera = cameraObject.AddComponent<SimpleThirdPersonCamera>();
        followCamera.target = player.transform;
        followCamera.distance = 6.3f;
        playerController.cameraTransform = cameraObject.transform;
        cameraObject.transform.position = new Vector3(0f, 4.5f, -9f);
        cameraObject.transform.LookAt(player.transform.position + Vector3.up * 1.2f);

        GameObject lightObject = new GameObject("Directional Light");
        Light light = lightObject.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.2f;
        lightObject.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        NpcAgentMarker amiya = CreateNpc("NPC_Amiya_Capsule", "arknights_amiya", "阿米娅", new Vector3(-4f, 1f, 3.5f), amiyaMaterial);
        NpcAgentMarker yae = CreateNpc("NPC_YaeMiko_Capsule", "genshin_yae_miko", "八重神子", new Vector3(0f, 1f, 5.5f), yaeMaterial);
        NpcAgentMarker jinhsi = CreateNpc("NPC_Jinhsi_Capsule", "wuwa_jinhsi", "今汐", new Vector3(4f, 1f, 3.5f), jinhsiMaterial);

        GameObject canvas = CreateScreenCanvas(out TMP_InputField inputField, out Button sendButton, out TMP_Text currentNpcLabel);
        GameObject dialogueSystem = new GameObject("DialogueSystem");
        DialogueRangeDetector rangeDetector = dialogueSystem.AddComponent<DialogueRangeDetector>();
        rangeDetector.player = player.transform;
        rangeDetector.currentNpcLabel = currentNpcLabel;

        NpcDialogueClient dialogueClient = dialogueSystem.AddComponent<NpcDialogueClient>();
        dialogueClient.endpoint = "http://127.0.0.1:8008/api/v1/dialogue";
        dialogueClient.playerBubble = playerBubbleAnchor.GetComponentInChildren<SpeechBubbleController>();

        PlayerChatInput chatInput = dialogueSystem.AddComponent<PlayerChatInput>();
        chatInput.inputField = inputField;
        chatInput.sendButton = sendButton;
        chatInput.rangeDetector = rangeDetector;
        chatInput.dialogueClient = dialogueClient;
        chatInput.playerController = playerController;
        chatInput.followCamera = followCamera;

        Selection.objects = new Object[] { player, amiya.gameObject, yae.gameObject, jinhsi.gameObject, canvas, dialogueSystem };
        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
    }

    [MenuItem("NPC Demo/Validate Whitebox Scene")]
    public static void ValidateWhiteboxScene()
    {
        if (!File.Exists(ScenePath))
        {
            throw new FileNotFoundException($"Whitebox scene does not exist at {ScenePath}.");
        }

        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

        GameObject player = RequireObject("PlayerCapsule");
        WhiteboxPlayerController playerController = RequireComponent<WhiteboxPlayerController>(player);
        RequireComponent<CharacterController>(player);

        RequireNpc("NPC_Amiya_Capsule", "arknights_amiya");
        RequireNpc("NPC_YaeMiko_Capsule", "genshin_yae_miko");
        RequireNpc("NPC_Jinhsi_Capsule", "wuwa_jinhsi");

        GameObject cameraObject = RequireObject("Main Camera");
        SimpleThirdPersonCamera camera = RequireComponent<SimpleThirdPersonCamera>(cameraObject);
        Require(camera.target == player.transform, "Main camera target is not the player.");

        GameObject dialogueSystem = RequireObject("DialogueSystem");
        DialogueRangeDetector rangeDetector = RequireComponent<DialogueRangeDetector>(dialogueSystem);
        Require(rangeDetector.player == player.transform, "Range detector player binding is missing.");
        NpcDialogueClient dialogueClient = RequireComponent<NpcDialogueClient>(dialogueSystem);
        Require(dialogueClient.endpoint == "http://127.0.0.1:8008/api/v1/dialogue", "Dialogue endpoint is not the local FastAPI endpoint.");
        PlayerChatInput chatInput = RequireComponent<PlayerChatInput>(dialogueSystem);
        Require(chatInput.playerController == playerController, "Chat input is not bound to the player controller.");
        Require(chatInput.followCamera == camera, "Chat input is not bound to the follow camera.");

        bool sceneInBuildSettings = false;
        foreach (EditorBuildSettingsScene buildScene in EditorBuildSettings.scenes)
        {
            if (buildScene.enabled && buildScene.path == ScenePath)
            {
                sceneInBuildSettings = true;
                break;
            }
        }
        Require(sceneInBuildSettings, "Whitebox scene is not enabled in Build Settings.");

        Debug.Log("Whitebox scene validation passed.");
    }

    private static NpcAgentMarker CreateNpc(string objectName, string npcId, string displayName, Vector3 position, Material material)
    {
        GameObject npc = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        npc.name = objectName;
        npc.transform.position = position;
        npc.GetComponent<Renderer>().sharedMaterial = material;

        NpcAgentMarker marker = npc.AddComponent<NpcAgentMarker>();
        marker.npcId = npcId;
        marker.displayName = displayName;
        marker.interactionRadius = 3f;
        marker.bubbleAnchor = CreateBubbleAnchor(npc.transform, "BubbleAnchor", new Vector3(0f, 2.95f, 0f));
        CreateNameplate(npc.transform, displayName, new Vector3(0f, 2.25f, 0f));
        return marker;
    }

    private static void RequireNpc(string objectName, string expectedNpcId)
    {
        GameObject npc = RequireObject(objectName);
        NpcAgentMarker marker = RequireComponent<NpcAgentMarker>(npc);
        Require(marker.npcId == expectedNpcId, $"{objectName} has unexpected npcId '{marker.npcId}'.");
        Require(marker.bubbleAnchor != null, $"{objectName} is missing a bubble anchor.");
        Require(marker.bubbleAnchor.GetComponentInChildren<SpeechBubbleController>() != null, $"{objectName} is missing a speech bubble.");
        Transform nameplate = npc.transform.Find("Nameplate");
        Require(nameplate != null, $"{objectName} is missing a nameplate.");
        Require(nameplate.GetComponentInChildren<TMP_Text>() != null, $"{objectName} nameplate is missing text.");
        Require(marker.bubbleAnchor.localPosition.y > nameplate.localPosition.y, $"{objectName} bubble should be above its nameplate.");
    }

    private static GameObject RequireObject(string objectName)
    {
        GameObject obj = GameObject.Find(objectName);
        Require(obj != null, $"Scene object '{objectName}' was not found.");
        return obj;
    }

    private static T RequireComponent<T>(GameObject obj) where T : Component
    {
        T component = obj.GetComponent<T>();
        Require(component != null, $"{obj.name} is missing component {typeof(T).Name}.");
        return component;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition)
        {
            throw new System.InvalidOperationException(message);
        }
    }

    private static Transform CreateBubbleAnchor(Transform parent, string objectName, Vector3 localPosition)
    {
        GameObject anchor = new GameObject(objectName);
        anchor.transform.SetParent(parent, false);
        anchor.transform.localPosition = localPosition;
        anchor.transform.localRotation = Quaternion.identity;
        anchor.transform.localScale = Vector3.one;

        GameObject bubbleCanvas = new GameObject("SpeechBubbleCanvas");
        bubbleCanvas.transform.SetParent(anchor.transform, false);
        bubbleCanvas.transform.localPosition = Vector3.zero;
        bubbleCanvas.transform.localRotation = Quaternion.identity;
        bubbleCanvas.transform.localScale = Vector3.one * 0.01f;

        Canvas canvas = bubbleCanvas.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;
        CanvasGroup group = bubbleCanvas.AddComponent<CanvasGroup>();
        group.alpha = 0f;

        RectTransform canvasRect = bubbleCanvas.GetComponent<RectTransform>();
        canvasRect.sizeDelta = new Vector2(260f, 86f);

        GameObject background = new GameObject("BubbleBackground");
        background.transform.SetParent(bubbleCanvas.transform, false);
        RectTransform backgroundRect = background.AddComponent<RectTransform>();
        backgroundRect.anchorMin = Vector2.zero;
        backgroundRect.anchorMax = Vector2.one;
        backgroundRect.offsetMin = Vector2.zero;
        backgroundRect.offsetMax = Vector2.zero;
        Image image = background.AddComponent<Image>();
        image.color = new Color(1f, 1f, 1f, 0.88f);

        GameObject textObject = new GameObject("BubbleText");
        textObject.transform.SetParent(bubbleCanvas.transform, false);
        RectTransform textRect = textObject.AddComponent<RectTransform>();
        textRect.anchorMin = Vector2.zero;
        textRect.anchorMax = Vector2.one;
        textRect.offsetMin = new Vector2(12f, 10f);
        textRect.offsetMax = new Vector2(-12f, -10f);
        TMP_Text text = textObject.AddComponent<TextMeshProUGUI>();
        text.text = "";
        text.fontSize = 24f;
        text.alignment = TextAlignmentOptions.Center;
        text.color = Color.black;
        text.textWrappingMode = TextWrappingModes.Normal;

        SpeechBubbleController bubble = bubbleCanvas.AddComponent<SpeechBubbleController>();
        bubble.bubbleText = text;
        bubble.canvasGroup = group;
        return anchor.transform;
    }

    private static void CreateNameplate(Transform parent, string displayName, Vector3 localPosition)
    {
        GameObject plate = new GameObject("Nameplate");
        plate.transform.SetParent(parent, false);
        plate.transform.localPosition = localPosition;
        plate.transform.localRotation = Quaternion.identity;
        plate.transform.localScale = Vector3.one * 0.01f;

        Canvas canvas = plate.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.WorldSpace;
        plate.AddComponent<BillboardToCamera>();
        RectTransform rect = plate.GetComponent<RectTransform>();
        rect.sizeDelta = new Vector2(160f, 34f);

        GameObject background = new GameObject("NameplateBackground");
        background.transform.SetParent(plate.transform, false);
        RectTransform backgroundRect = background.AddComponent<RectTransform>();
        backgroundRect.anchorMin = Vector2.zero;
        backgroundRect.anchorMax = Vector2.one;
        backgroundRect.offsetMin = Vector2.zero;
        backgroundRect.offsetMax = Vector2.zero;
        Image image = background.AddComponent<Image>();
        image.color = new Color(0f, 0f, 0f, 0.48f);

        GameObject textObject = new GameObject("NameplateText");
        textObject.transform.SetParent(plate.transform, false);
        RectTransform textRect = textObject.AddComponent<RectTransform>();
        textRect.anchorMin = Vector2.zero;
        textRect.anchorMax = Vector2.one;
        textRect.offsetMin = new Vector2(8f, 2f);
        textRect.offsetMax = new Vector2(-8f, -2f);

        TMP_Text text = textObject.AddComponent<TextMeshProUGUI>();
        text.text = displayName;
        text.fontSize = 23f;
        text.alignment = TextAlignmentOptions.Center;
        text.color = Color.white;
    }

    private static GameObject CreateScreenCanvas(out TMP_InputField inputField, out Button sendButton, out TMP_Text currentNpcLabel)
    {
        GameObject eventSystem = new GameObject("EventSystem");
        eventSystem.AddComponent<EventSystem>();
        eventSystem.AddComponent<StandaloneInputModule>();

        GameObject canvasObject = new GameObject("Canvas");
        Canvas canvas = canvasObject.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1280f, 720f);
        canvasObject.AddComponent<GraphicRaycaster>();

        currentNpcLabel = CreateUiText(canvasObject.transform, "CurrentNpcLabel", "未进入 NPC 对话范围", new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 116f), new Vector2(540f, 38f), 22f);
        inputField = CreateInputField(canvasObject.transform);
        sendButton = CreateButton(canvasObject.transform, "SendButton", "发送", new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(382f, 58f), new Vector2(120f, 48f));
        return canvasObject;
    }

    private static TMP_Text CreateUiText(Transform parent, string name, string value, Vector2 anchorMin, Vector2 anchorMax, Vector2 position, Vector2 size, float fontSize)
    {
        GameObject textObject = new GameObject(name);
        textObject.transform.SetParent(parent, false);
        RectTransform rect = textObject.AddComponent<RectTransform>();
        rect.anchorMin = anchorMin;
        rect.anchorMax = anchorMax;
        rect.anchoredPosition = position;
        rect.sizeDelta = size;
        TMP_Text text = textObject.AddComponent<TextMeshProUGUI>();
        text.text = value;
        text.fontSize = fontSize;
        text.alignment = TextAlignmentOptions.Center;
        text.color = Color.white;
        return text;
    }

    private static TMP_InputField CreateInputField(Transform parent)
    {
        GameObject root = new GameObject("ChatInput");
        root.transform.SetParent(parent, false);
        RectTransform rect = root.AddComponent<RectTransform>();
        rect.anchorMin = new Vector2(0.5f, 0f);
        rect.anchorMax = new Vector2(0.5f, 0f);
        rect.anchoredPosition = new Vector2(-70f, 58f);
        rect.sizeDelta = new Vector2(760f, 48f);
        Image background = root.AddComponent<Image>();
        background.color = new Color(0.08f, 0.09f, 0.1f, 0.92f);

        GameObject viewport = new GameObject("TextViewport");
        viewport.transform.SetParent(root.transform, false);
        RectTransform viewportRect = viewport.AddComponent<RectTransform>();
        viewportRect.anchorMin = Vector2.zero;
        viewportRect.anchorMax = Vector2.one;
        viewportRect.offsetMin = new Vector2(14f, 6f);
        viewportRect.offsetMax = new Vector2(-14f, -6f);
        viewport.AddComponent<RectMask2D>();

        TMP_Text text = CreateUiText(viewport.transform, "Text", "", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 22f);
        text.alignment = TextAlignmentOptions.MidlineLeft;
        text.color = Color.white;
        RectTransform textRect = text.GetComponent<RectTransform>();
        textRect.offsetMin = Vector2.zero;
        textRect.offsetMax = Vector2.zero;

        TMP_Text placeholder = CreateUiText(viewport.transform, "Placeholder", "靠近 NPC 后按 Enter 输入文字", Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 22f);
        placeholder.alignment = TextAlignmentOptions.MidlineLeft;
        placeholder.color = new Color(1f, 1f, 1f, 0.45f);

        TMP_InputField input = root.AddComponent<TMP_InputField>();
        input.textViewport = viewportRect;
        input.textComponent = text;
        input.placeholder = placeholder;
        input.lineType = TMP_InputField.LineType.SingleLine;
        input.characterLimit = 120;
        return input;
    }

    private static Button CreateButton(Transform parent, string name, string label, Vector2 anchorMin, Vector2 anchorMax, Vector2 position, Vector2 size)
    {
        GameObject root = new GameObject(name);
        root.transform.SetParent(parent, false);
        RectTransform rect = root.AddComponent<RectTransform>();
        rect.anchorMin = anchorMin;
        rect.anchorMax = anchorMax;
        rect.anchoredPosition = position;
        rect.sizeDelta = size;
        Image image = root.AddComponent<Image>();
        image.color = new Color(0.18f, 0.42f, 0.86f, 0.95f);
        Button button = root.AddComponent<Button>();

        TMP_Text text = CreateUiText(root.transform, "Label", label, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 22f);
        text.alignment = TextAlignmentOptions.Center;
        return button;
    }

    private static Material CreateMaterial(string materialName, Color color)
    {
        Directory.CreateDirectory("Assets/Materials");
        string path = $"Assets/Materials/{materialName}.mat";
        Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard"));
            AssetDatabase.CreateAsset(material, path);
        }
        material.color = color;
        return material;
    }
}
