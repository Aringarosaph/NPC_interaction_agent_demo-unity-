using UnityEngine;

public class SimpleThirdPersonCamera : MonoBehaviour
{
    public Transform target;
    public float distance = 6.0f;
    public float followSharpness = 12f;
    public float lookHeight = 1.2f;
    public float mouseSensitivity = 2.2f;
    public float minPitch = -18f;
    public float maxPitch = 68f;
    public bool lookEnabled = true;

    private float yaw;
    private float pitch = 24f;

    private void Start()
    {
        yaw = transform.eulerAngles.y;
        SetLookEnabled(true);
    }

    private void LateUpdate()
    {
        if (target == null) return;

        if (lookEnabled)
        {
            yaw += Input.GetAxis("Mouse X") * mouseSensitivity;
            pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * mouseSensitivity, minPitch, maxPitch);
        }

        Quaternion orbitRotation = Quaternion.Euler(pitch, yaw, 0f);
        Vector3 lookTarget = target.position + Vector3.up * lookHeight;
        Vector3 desiredPosition = lookTarget + orbitRotation * new Vector3(0f, 0f, -distance);
        transform.position = Vector3.Lerp(transform.position, desiredPosition, 1f - Mathf.Exp(-followSharpness * Time.deltaTime));
        transform.rotation = Quaternion.LookRotation(lookTarget - transform.position, Vector3.up);
    }

    public void SetLookEnabled(bool enabled)
    {
        lookEnabled = enabled;
        Cursor.lockState = enabled ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !enabled;
    }
}
