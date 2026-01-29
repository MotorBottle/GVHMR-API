"""
Skeleton renderer for GVHMR - draws 3D joint positions on video frames
"""
import cv2
import numpy as np
import torch


# SMPL 24 joints skeleton structure
# Based on SMPL joint hierarchy
SMPL_SKELETON = [
    [0, 1],   # Pelvis -> Left Hip
    [0, 2],   # Pelvis -> Right Hip
    [0, 3],   # Pelvis -> Spine1
    [3, 6],   # Spine1 -> Spine2
    [6, 9],   # Spine2 -> Spine3
    [9, 12],  # Spine3 -> Neck
    [12, 15], # Neck -> Head
    [9, 13],  # Spine3 -> Left Collar
    [13, 16], # Left Collar -> Left Shoulder
    [16, 18], # Left Shoulder -> Left Elbow
    [18, 20], # Left Elbow -> Left Wrist
    [20, 22], # Left Wrist -> Left Hand
    [9, 14],  # Spine3 -> Right Collar
    [14, 17], # Right Collar -> Right Shoulder
    [17, 19], # Right Shoulder -> Right Elbow
    [19, 21], # Right Elbow -> Right Wrist
    [21, 23], # Right Wrist -> Right Hand
    [1, 4],   # Left Hip -> Left Knee
    [4, 7],   # Left Knee -> Left Ankle
    [7, 10],  # Left Ankle -> Left Foot
    [2, 5],   # Right Hip -> Right Knee
    [5, 8],   # Right Knee -> Right Ankle
    [8, 11],  # Right Ankle -> Right Foot
]

# Joint names for reference
SMPL_JOINT_NAMES = [
    "Pelvis",           # 0
    "Left_Hip",         # 1
    "Right_Hip",        # 2
    "Spine1",           # 3
    "Left_Knee",        # 4
    "Right_Knee",       # 5
    "Spine2",           # 6
    "Left_Ankle",       # 7
    "Right_Ankle",      # 8
    "Spine3",           # 9
    "Left_Foot",        # 10
    "Right_Foot",       # 11
    "Neck",             # 12
    "Left_Collar",      # 13
    "Right_Collar",     # 14
    "Head",             # 15
    "Left_Shoulder",    # 16
    "Right_Shoulder",   # 17
    "Left_Elbow",       # 18
    "Right_Elbow",      # 19
    "Left_Wrist",       # 20
    "Right_Wrist",      # 21
    "Left_Hand",        # 22
    "Right_Hand",       # 23
]


def project_joints_to_2d(joints_3d, K):
    """
    Project 3D joints to 2D image coordinates

    Args:
        joints_3d: (J, 3) or (B, J, 3) - 3D joint positions
        K: (3, 3) or (B, 3, 3) - Camera intrinsic matrix

    Returns:
        joints_2d: (J, 2) or (B, J, 2) - 2D projected coordinates
    """
    if joints_3d.dim() == 2:
        # Single frame: (J, 3)
        # Homogeneous coordinates
        joints_homo = joints_3d  # (J, 3)
        # Project: [u, v, d] = K @ [x, y, z]
        projected = torch.matmul(K, joints_homo.T)  # (3, J)
        # Normalize by depth
        joints_2d = projected[:2] / projected[2:3]  # (2, J)
        return joints_2d.T  # (J, 2)
    else:
        # Batch: (B, J, 3)
        B, J, _ = joints_3d.shape
        projected = torch.matmul(K, joints_3d.transpose(1, 2))  # (B, 3, J)
        joints_2d = projected[:, :2] / projected[:, 2:3]  # (B, 2, J)
        return joints_2d.transpose(1, 2)  # (B, J, 2)


def draw_smpl_skeleton_on_image(img, joints_2d, draw_joints=True, draw_bones=True,
                                  joint_color=(0, 255, 0), bone_color=(0, 200, 0),
                                  joint_radius=5, bone_thickness=3):
    """
    Draw SMPL skeleton on image

    Args:
        img: (H, W, 3) numpy array
        joints_2d: (24, 2) 2D joint positions
        draw_joints: bool, whether to draw joint circles
        draw_bones: bool, whether to draw bone lines
        joint_color: (B, G, R) tuple
        bone_color: (B, G, R) tuple
        joint_radius: int
        bone_thickness: int

    Returns:
        img_out: (H, W, 3) numpy array with skeleton drawn
    """
    img_out = img.copy()

    if isinstance(joints_2d, torch.Tensor):
        joints_2d = joints_2d.cpu().numpy()

    # Draw bones first (so joints are on top)
    if draw_bones:
        for bone in SMPL_SKELETON:
            j1_idx, j2_idx = bone
            j1 = joints_2d[j1_idx].astype(int)
            j2 = joints_2d[j2_idx].astype(int)

            # Only draw if both joints are within image bounds
            h, w = img.shape[:2]
            if (0 <= j1[0] < w and 0 <= j1[1] < h and
                0 <= j2[0] < w and 0 <= j2[1] < h):
                cv2.line(img_out, tuple(j1), tuple(j2), bone_color, bone_thickness)

    # Draw joints
    if draw_joints:
        for joint in joints_2d:
            j = joint.astype(int)
            h, w = img.shape[:2]
            if 0 <= j[0] < w and 0 <= j[1] < h:
                cv2.circle(img_out, tuple(j), joint_radius, joint_color, -1)

    return img_out


def draw_smpl_skeleton_batch(imgs, joints_2d_batch, **kwargs):
    """
    Draw SMPL skeleton on batch of images

    Args:
        imgs: list of (H, W, 3) numpy arrays
        joints_2d_batch: (B, 24, 2) 2D joint positions
        **kwargs: passed to draw_smpl_skeleton_on_image

    Returns:
        imgs_out: list of (H, W, 3) numpy arrays with skeletons
    """
    if isinstance(joints_2d_batch, torch.Tensor):
        joints_2d_batch = joints_2d_batch.cpu().numpy()

    imgs_out = []
    for i, img in enumerate(imgs):
        img_out = draw_smpl_skeleton_on_image(img, joints_2d_batch[i], **kwargs)
        imgs_out.append(img_out)

    return imgs_out
