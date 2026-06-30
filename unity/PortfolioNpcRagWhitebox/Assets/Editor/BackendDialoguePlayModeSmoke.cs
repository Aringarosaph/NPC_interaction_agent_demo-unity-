using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class BackendDialoguePlayModeSmoke
{
    private const string ScenePath = "Assets/Scenes/Scene_PortfolioNpcRag.unity";
    private const string PendingKey = "BackendDialoguePlayModeSmoke.Pending";
    private const string CompleteKey = "BackendDialoguePlayModeSmoke.Complete";
    private const string PassedKey = "BackendDialoguePlayModeSmoke.Passed";
    private const string MessageKey = "BackendDialoguePlayModeSmoke.Message";
    private const string RunnerStartedKey = "BackendDialoguePlayModeSmoke.RunnerStarted";
    private const string DeadlineKey = "BackendDialoguePlayModeSmoke.Deadline";
    private const float TimeoutSeconds = 60f;

    static BackendDialoguePlayModeSmoke()
    {
        EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
        EditorApplication.update += OnEditorUpdate;
    }

    [MenuItem("NPC Demo/Run Backend PlayMode Smoke")]
    public static void Run()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode)
        {
            FailBeforePlayMode("Unity is already entering or running Play Mode.");
            return;
        }

        SessionState.SetBool(PendingKey, true);
        SessionState.SetBool(CompleteKey, false);
        SessionState.SetBool(PassedKey, false);
        SessionState.SetBool(RunnerStartedKey, false);
        SessionState.SetString(MessageKey, string.Empty);
        SessionState.SetFloat(DeadlineKey, (float)EditorApplication.timeSinceStartup + TimeoutSeconds);

        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        EditorApplication.EnterPlaymode();
    }

    private static void OnPlayModeStateChanged(PlayModeStateChange state)
    {
        if (!SessionState.GetBool(PendingKey, false))
        {
            return;
        }

        if (state == PlayModeStateChange.EnteredPlayMode)
        {
            StartRunner();
        }
        else if (state == PlayModeStateChange.EnteredEditMode)
        {
            ExitBatchModeIfComplete();
        }
    }

    private static void OnEditorUpdate()
    {
        if (!SessionState.GetBool(PendingKey, false) || SessionState.GetBool(CompleteKey, false))
        {
            return;
        }

        float deadline = SessionState.GetFloat(DeadlineKey, 0f);
        if (deadline > 0f && EditorApplication.timeSinceStartup > deadline)
        {
            Finish(false, "Unity backend Play Mode smoke timed out.");
        }
    }

    private static void StartRunner()
    {
        if (SessionState.GetBool(RunnerStartedKey, false))
        {
            return;
        }

        SessionState.SetBool(RunnerStartedKey, true);
        GameObject runnerObject = new GameObject("BackendDialoguePlayModeSmokeRunner");
        BackendDialoguePlayModeSmokeRunner runner = runnerObject.AddComponent<BackendDialoguePlayModeSmokeRunner>();
        runner.StartCoroutine(runner.Run(Finish));
    }

    private static void Finish(bool passed, string message)
    {
        if (SessionState.GetBool(CompleteKey, false))
        {
            return;
        }

        SessionState.SetBool(CompleteKey, true);
        SessionState.SetBool(PassedKey, passed);
        SessionState.SetString(MessageKey, message);

        if (passed)
        {
            Debug.Log($"Unity backend Play Mode smoke passed. {message}");
        }
        else
        {
            Debug.LogError($"Unity backend Play Mode smoke failed. {message}");
        }

        if (EditorApplication.isPlaying)
        {
            EditorApplication.ExitPlaymode();
        }
        else
        {
            ExitBatchModeIfComplete();
        }
    }

    private static void ExitBatchModeIfComplete()
    {
        if (!SessionState.GetBool(CompleteKey, false))
        {
            return;
        }

        bool passed = SessionState.GetBool(PassedKey, false);
        string message = SessionState.GetString(MessageKey, string.Empty);
        WhiteboxSceneBuilder.ClearChineseFontDynamicData();
        ClearSession();

        if (Application.isBatchMode)
        {
            EditorApplication.Exit(passed ? 0 : 1);
            return;
        }

        if (!passed)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void FailBeforePlayMode(string message)
    {
        Debug.LogError(message);
        if (Application.isBatchMode)
        {
            ClearSession();
            EditorApplication.Exit(1);
        }
        else
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void ClearSession()
    {
        SessionState.EraseBool(PendingKey);
        SessionState.EraseBool(CompleteKey);
        SessionState.EraseBool(PassedKey);
        SessionState.EraseBool(RunnerStartedKey);
        SessionState.EraseString(MessageKey);
        SessionState.EraseFloat(DeadlineKey);
    }
}
