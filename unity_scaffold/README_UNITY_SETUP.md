# Unity Scaffold Setup

1. 新建 Unity 3D 项目。
2. 安装 TextMeshPro。
3. 创建一个白盒场景：主角 Capsule + 三个 NPC Capsule。
4. 把 `Assets/Scripts/NpcDialogue/` 里的脚本放进项目。
5. NPC 上挂 `NpcAgentMarker`，分别填写：
   - `arknights_amiya`
   - `genshin_yae_miko`
   - `wuwa_jinhsi`
6. 场景中创建 `DialogueSystem` 空物体，挂：
   - `DialogueRangeDetector`
   - `NpcDialogueClient`
   - `PlayerChatInput`
7. Canvas 上创建 TMP_InputField、Button、CurrentNpcLabel。
8. 主角和每个 NPC 下创建 `BubbleAnchor` 空物体，挂世界空间气泡 prefab 或用 `SpeechBubbleController` 绑定文本。
9. 启动本地后端后运行 Unity。
