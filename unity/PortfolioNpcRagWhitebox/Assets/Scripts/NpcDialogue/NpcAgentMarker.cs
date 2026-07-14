using UnityEngine;

public class NpcAgentMarker : MonoBehaviour
{
    public string npcId;
    public string displayName;
    public float interactionRadius = 3f;
    public Transform rangeCenter;
    public Transform bubbleAnchor;
    public NpcPerformanceController performanceController;

    public Vector3 RangeCenterPosition => rangeCenter != null ? rangeCenter.position : transform.position;

    private void OnDrawGizmosSelected()
    {
        Gizmos.DrawWireSphere(RangeCenterPosition, interactionRadius);
    }
}
