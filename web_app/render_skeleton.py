"""
Standalone skeleton renderer for GVHMR results
Reads hmr4d_results.pt and creates skeleton visualization videos
"""
import sys
sys.path.insert(0, '/app/gvhmr')

import torch
from pathlib import Path
from tqdm import tqdm
from einops import einsum

# GVHMR imports
from hmr4d.utils.smplx_utils import make_smplx
from hmr4d.utils.video_io_utils import get_video_lwh, get_writer, get_video_reader
from hmr4d.utils.net_utils import to_cuda

# Local skeleton drawing utilities
from skeleton_renderer import project_joints_to_2d, draw_smpl_skeleton_on_image

CRF = 23  # Video compression


def render_skeleton_incam(cfg, output_skeleton_path):
    """
    Render skeleton overlay on input video (in-camera view)

    Args:
        cfg: Hydra config object with paths
        output_skeleton_path: Path to save skeleton video
    """
    output_skeleton_path = Path(output_skeleton_path)
    if output_skeleton_path.exists():
        print(f"[Render Skeleton Incam] Video already exists at {output_skeleton_path}")
        return

    # Load results
    pred = torch.load(cfg.paths.hmr4d_results)

    # Load SMPL model
    smplx = make_smplx("supermotion").cuda()
    smplx2smpl = torch.load("/app/gvhmr/hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
    J_regressor = torch.load("/app/gvhmr/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()

    # Get SMPL vertices in camera space
    smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
    pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])

    # Extract joints from vertices using J_regressor
    joints_incam = einsum(J_regressor, pred_c_verts, "j v, l v i -> l j i")  # (L, 24, 3)

    # Get camera intrinsics
    K = pred["K_fullimg"][0].cuda()

    # Project joints to 2D
    joints_2d = []
    for i in range(len(joints_incam)):
        j2d = project_joints_to_2d(joints_incam[i], K)
        joints_2d.append(j2d)
    joints_2d = torch.stack(joints_2d)  # (L, 24, 2)

    # Render skeleton on video
    video_path = cfg.video_path
    length, width, height = get_video_lwh(video_path)

    reader = get_video_reader(video_path)
    writer = get_writer(str(output_skeleton_path), fps=30, crf=CRF)

    # Use minimum of video length and joints length to avoid index errors
    num_frames = min(length, len(joints_2d))

    for i, img_raw in tqdm(enumerate(reader), total=num_frames, desc="Rendering Skeleton Incam"):
        if i >= num_frames:
            break  # Stop if we run out of joint data

        # Draw skeleton
        img = draw_smpl_skeleton_on_image(
            img_raw,
            joints_2d[i],
            draw_joints=True,
            draw_bones=True,
            joint_color=(0, 255, 0),   # Green joints
            bone_color=(0, 200, 0),     # Slightly darker green bones
            joint_radius=6,
            bone_thickness=3
        )
        writer.write_frame(img)

    writer.close()
    reader.close()
    print(f"[Render Skeleton Incam] Saved to {output_skeleton_path}")


def render_skeleton_only(cfg, output_skeleton_path):
    """
    Render skeleton on black background (no video overlay)

    Args:
        cfg: Hydra config object with paths
        output_skeleton_path: Path to save skeleton video
    """
    import numpy as np

    output_skeleton_path = Path(output_skeleton_path)
    if output_skeleton_path.exists():
        print(f"[Render Skeleton Only] Video already exists at {output_skeleton_path}")
        return

    # Load results
    pred = torch.load(cfg.paths.hmr4d_results)

    # Load SMPL model
    smplx = make_smplx("supermotion").cuda()
    smplx2smpl = torch.load("/app/gvhmr/hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
    J_regressor = torch.load("/app/gvhmr/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()

    # Get SMPL vertices in camera space
    smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
    pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])

    # Extract joints from vertices
    joints_incam = einsum(J_regressor, pred_c_verts, "j v, l v i -> l j i")  # (L, 24, 3)

    # Get camera intrinsics and video dimensions
    K = pred["K_fullimg"][0].cuda()
    video_path = cfg.video_path
    length, width, height = get_video_lwh(video_path)

    # Project joints to 2D
    joints_2d = []
    for i in range(len(joints_incam)):
        j2d = project_joints_to_2d(joints_incam[i], K)
        joints_2d.append(j2d)
    joints_2d = torch.stack(joints_2d)  # (L, 24, 2)

    # Render skeleton on black background
    writer = get_writer(str(output_skeleton_path), fps=30, crf=CRF)

    # Use minimum of video length and joints length to avoid index errors
    num_frames = min(length, len(joints_2d))

    for i in tqdm(range(num_frames), desc="Rendering Skeleton Only"):
        # Create black background
        black_bg = np.zeros((height, width, 3), dtype=np.uint8)

        # Draw skeleton
        img = draw_smpl_skeleton_on_image(
            black_bg,
            joints_2d[i],
            draw_joints=True,
            draw_bones=True,
            joint_color=(0, 255, 0),   # Green joints
            bone_color=(0, 200, 0),     # Green bones
            joint_radius=8,             # Larger for visibility
            bone_thickness=4
        )
        writer.write_frame(img)

    writer.close()
    print(f"[Render Skeleton Only] Saved to {output_skeleton_path}")


def save_joints_json(cfg, output_json_path):
    """
    Save joint positions to JSON format for external use

    Args:
        cfg: Hydra config object with paths
        output_json_path: Path to save JSON file
    """
    import json

    output_json_path = Path(output_json_path)
    if output_json_path.exists():
        print(f"[Save Joints JSON] File already exists at {output_json_path}")
        return

    # Load results
    pred = torch.load(cfg.paths.hmr4d_results)

    # Load SMPL model
    smplx = make_smplx("supermotion").cuda()
    smplx2smpl = torch.load("/app/gvhmr/hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
    J_regressor = torch.load("/app/gvhmr/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()

    # Get SMPL vertices in camera space
    smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
    pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])

    # Extract joints from vertices
    joints_incam = einsum(J_regressor, pred_c_verts, "j v, l v i -> l j i")  # (L, 24, 3)

    # Also get global joints
    smplx_out_global = smplx(**to_cuda(pred["smpl_params_global"]))
    pred_g_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out_global.vertices])
    joints_global = einsum(J_regressor, pred_g_verts, "j v, l v i -> l j i")  # (L, 24, 3)

    # Convert to JSON-serializable format
    from skeleton_renderer import SMPL_JOINT_NAMES, SMPL_SKELETON

    data = {
        "num_frames": int(joints_incam.shape[0]),
        "num_joints": 24,
        "joint_names": SMPL_JOINT_NAMES,
        "skeleton_connections": SMPL_SKELETON,
        "fps": 30,
        "joints_camera_space": joints_incam.cpu().numpy().tolist(),  # (L, 24, 3)
        "joints_global_space": joints_global.cpu().numpy().tolist(),  # (L, 24, 3)
        "camera_intrinsics": pred["K_fullimg"][0].cpu().numpy().tolist(),  # (3, 3)
    }

    with open(output_json_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"[Save Joints JSON] Saved to {output_json_path}")


if __name__ == "__main__":
    # This script is meant to be imported and used by modified demo.py
    # But can be run standalone if cfg is provided
    print("Skeleton renderer utility loaded")
