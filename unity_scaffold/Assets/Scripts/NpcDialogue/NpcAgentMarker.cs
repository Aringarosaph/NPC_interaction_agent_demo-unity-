using UnityEngine;

public class NpcAgentMarker : MonoBehaviour
{
    public string npcId;
    public string displayName;
    public float interactionRadius = 3f;
    public Transform bubbleAnchor;

    private void OnDrawGizmosSelected()
    {
        Gizmos.DrawWireSphere(transform.position, interactionRadius);
    }
}
