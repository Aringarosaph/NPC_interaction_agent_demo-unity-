using UnityEngine;

[RequireComponent(typeof(CharacterController))]
public class WhiteboxPlayerController : MonoBehaviour
{
    public float moveSpeed = 4.5f;
    public float rotationSpeed = 540f;
    public Transform cameraTransform;
    public bool controlsEnabled = true;

    private CharacterController controller;
    private float verticalVelocity;

    private void Awake()
    {
        controller = GetComponent<CharacterController>();
    }

    private void Update()
    {
        if (!controlsEnabled)
        {
            ApplyGravity(Vector3.zero);
            return;
        }

        float horizontal = Input.GetAxisRaw("Horizontal");
        float vertical = Input.GetAxisRaw("Vertical");
        Vector3 input = new Vector3(horizontal, 0f, vertical);
        input = Vector3.ClampMagnitude(input, 1f);

        Vector3 move = input;
        if (cameraTransform != null)
        {
            Vector3 forward = cameraTransform.forward;
            Vector3 right = cameraTransform.right;
            forward.y = 0f;
            right.y = 0f;
            forward.Normalize();
            right.Normalize();
            move = forward * input.z + right * input.x;
        }

        if (move.sqrMagnitude > 0.001f)
        {
            Quaternion targetRotation = Quaternion.LookRotation(move);
            transform.rotation = Quaternion.RotateTowards(transform.rotation, targetRotation, rotationSpeed * Time.deltaTime);
        }

        ApplyGravity(move * moveSpeed);
    }

    private void ApplyGravity(Vector3 horizontalVelocity)
    {
        if (controller.isGrounded && verticalVelocity < 0f)
        {
            verticalVelocity = -1f;
        }
        verticalVelocity += Physics.gravity.y * Time.deltaTime;

        horizontalVelocity.y = verticalVelocity;
        controller.Move(horizontalVelocity * Time.deltaTime);
    }
}
