using UnityEngine;

public class SimpleThirdPersonCamera : MonoBehaviour
{
    public Transform target;
    public float distance = 6.0f;
    public float minDistance = 2.2f;
    public float maxDistance = 9f;
    public float zoomSensitivity = 0.8f;
    public float zoomSharpness = 12f;
    public float followSharpness = 12f;
    public float lookHeight = 1.2f;
    public float firstPersonEyeHeight = 1.46f;
    public float firstPersonForwardOffset = 0.18f;
    public float mouseSensitivity = 2.2f;
    public float minPitch = -18f;
    public float maxPitch = 68f;
    public bool lookEnabled = true;

    private float yaw;
    private float pitch = 24f;
    private float targetDistance;
    private bool firstPerson;

    public bool IsFirstPerson => firstPerson;
    public float ThirdPersonDistance => targetDistance;

    private void Start()
    {
        yaw = transform.eulerAngles.y;
        targetDistance = Mathf.Clamp(distance, minDistance, maxDistance);
        SetLookEnabled(true);
    }

    private void LateUpdate()
    {
        if (target == null) return;

        if (lookEnabled)
        {
            yaw += Input.GetAxis("Mouse X") * mouseSensitivity;
            pitch = Mathf.Clamp(pitch - Input.GetAxis("Mouse Y") * mouseSensitivity, minPitch, maxPitch);
            if (!firstPerson)
            {
                ApplyZoomInput(Input.mouseScrollDelta.y);
            }
        }

        Quaternion lookRotation = Quaternion.Euler(pitch, yaw, 0f);
        if (firstPerson)
        {
            transform.position = target.position + Vector3.up * firstPersonEyeHeight +
                                 target.forward * firstPersonForwardOffset;
            transform.rotation = lookRotation;
            return;
        }

        distance = Mathf.Lerp(distance, targetDistance, 1f - Mathf.Exp(-zoomSharpness * Time.deltaTime));
        Vector3 lookTarget = target.position + Vector3.up * lookHeight;
        Vector3 desiredPosition = lookTarget + lookRotation * new Vector3(0f, 0f, -distance);
        transform.position = Vector3.Lerp(transform.position, desiredPosition, 1f - Mathf.Exp(-followSharpness * Time.deltaTime));
        transform.rotation = Quaternion.LookRotation(lookTarget - transform.position, Vector3.up);
    }

    public void ToggleViewMode()
    {
        SetFirstPerson(!firstPerson);
    }

    public void SetFirstPerson(bool enabled)
    {
        firstPerson = enabled;
    }

    public void ApplyZoomInput(float scrollDelta)
    {
        if (Mathf.Abs(scrollDelta) < 0.001f) return;
        targetDistance = Mathf.Clamp(targetDistance - scrollDelta * zoomSensitivity, minDistance, maxDistance);
    }

    public void SetLookEnabled(bool enabled)
    {
        lookEnabled = enabled;
        Cursor.lockState = enabled ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !enabled;
    }
}
