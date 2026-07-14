using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class YaeMikoPerformancePlayModeSmoke
{
    private const string ScenePath = "Assets/Scenes/Scene_PortfolioNpcRag.unity";
    private const string PendingKey = "YaeMikoPerformanceSmoke.Pending";
    private const string CompleteKey = "YaeMikoPerformanceSmoke.Complete";
    private const string PassedKey = "YaeMikoPerformanceSmoke.Passed";
    private const string MessageKey = "YaeMikoPerformanceSmoke.Message";
    private const float TimeoutSeconds = 30f;

    static YaeMikoPerformancePlayModeSmoke()
    {
        EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
        EditorApplication.update += OnEditorUpdate;
    }

    [MenuItem("NPC Demo/Run Yae Miko Performance Smoke")]
    public static void Run()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
        {
            Finish(false, "Unity is already entering or running Play Mode.");
            return;
        }

        SessionState.SetBool(PendingKey, true);
        SessionState.SetBool(CompleteKey, false);
        SessionState.SetBool(PassedKey, false);
        SessionState.SetString(MessageKey, string.Empty);
        SessionState.SetFloat(PendingKey + ".Deadline", (float)EditorApplication.timeSinceStartup + TimeoutSeconds);
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        EditorApplication.EnterPlaymode();
    }

    private static void OnPlayModeStateChanged(PlayModeStateChange state)
    {
        if (!SessionState.GetBool(PendingKey, false)) return;
        if (state == PlayModeStateChange.EnteredPlayMode)
        {
            GameObject runnerObject = new GameObject("YaeMikoPerformanceSmokeRunner");
            YaeMikoPerformanceSmokeRunner runner = runnerObject.AddComponent<YaeMikoPerformanceSmokeRunner>();
            runner.StartCoroutine(runner.Run(Finish));
        }
        else if (state == PlayModeStateChange.EnteredEditMode)
        {
            ExitBatchModeIfComplete();
        }
    }

    private static void OnEditorUpdate()
    {
        if (!SessionState.GetBool(PendingKey, false) || SessionState.GetBool(CompleteKey, false)) return;
        if (EditorApplication.timeSinceStartup > SessionState.GetFloat(PendingKey + ".Deadline", 0f))
        {
            Finish(false, "Yae Miko performance smoke timed out.");
        }
    }

    private static void Finish(bool passed, string message)
    {
        if (SessionState.GetBool(CompleteKey, false)) return;
        SessionState.SetBool(CompleteKey, true);
        SessionState.SetBool(PassedKey, passed);
        SessionState.SetString(MessageKey, message);
        if (passed) Debug.Log($"Yae Miko performance smoke passed. {message}");
        else Debug.LogError($"Yae Miko performance smoke failed. {message}");

        if (EditorApplication.isPlaying) EditorApplication.ExitPlaymode();
        else ExitBatchModeIfComplete();
    }

    private static void ExitBatchModeIfComplete()
    {
        if (!SessionState.GetBool(CompleteKey, false)) return;
        bool passed = SessionState.GetBool(PassedKey, false);
        string message = SessionState.GetString(MessageKey, string.Empty);
        SessionState.EraseBool(PendingKey);
        SessionState.EraseBool(CompleteKey);
        SessionState.EraseBool(PassedKey);
        SessionState.EraseString(MessageKey);
        SessionState.EraseFloat(PendingKey + ".Deadline");
        WhiteboxSceneBuilder.ClearChineseFontDynamicData();

        if (Application.isBatchMode) EditorApplication.Exit(passed ? 0 : 1);
        else if (!passed) throw new InvalidOperationException(message);
    }
}
