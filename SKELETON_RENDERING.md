# Skeleton/Rig Rendering Feature

GVHMR can now output **skeleton visualizations** in addition to the standard body mesh rendering.

## What is Skeleton Rendering?

Instead of rendering a complete 3D body mesh, skeleton rendering shows:
- **24 SMPL joints** as colored points
- **Bone connections** as lines between joints
- Clean visualization of body pose and movement

This is useful for:
- Motion analysis and debugging
- Animation reference
- Understanding joint positions without mesh clutter
- Integration with animation software

## How to Use

### Web Interface

1. Upload your video as usual
2. **Check the "Render Skeleton" option** before processing
3. Process the video
4. Download results - you'll now get additional files:
   - `skeleton_incam.mp4` - Skeleton overlay on input video
   - `skeleton_only.mp4` - Skeleton on black background
   - `joints.json` - Joint positions in JSON format

### API (REST)

Add `render_skeleton: true` to the process request:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "static_camera": true,
    "render_skeleton": true
  }' \
  http://localhost:5000/process
```

### Python Script

Use the modified demo script directly:

```bash
docker exec gvhmr-app python /app/web_app/demo_with_skeleton.py \
  --video /app/uploads/video.mp4 \
  --output_root /app/results/video \
  -s
```

## Output Files

When skeleton rendering is enabled, you get these additional outputs:

### 1. skeleton_incam.mp4
- Skeleton overlay on the original input video
- Shows 24 SMPL joints and bone connections
- Green colored visualization
- Matches camera perspective of input video

### 2. skeleton_only.mp4
- Skeleton visualization on black background
- Same camera view as input
- Cleaner view without video distraction
- Useful for motion analysis

### 3. joints.json
JSON file containing:
```json
{
  "num_frames": 74,
  "num_joints": 24,
  "joint_names": ["Pelvis", "Left_Hip", "Right_Hip", ...],
  "skeleton_connections": [[0, 1], [0, 2], ...],
  "fps": 30,
  "joints_camera_space": [...],  // (frames, 24, 3)
  "joints_global_space": [...],  // (frames, 24, 3)
  "camera_intrinsics": [...]     // (3, 3)
}
```

**Use cases for JSON:**
- Import into 3D software (Blender, Maya)
- Custom visualization
- Motion analysis algorithms
- Machine learning datasets

## SMPL Skeleton Structure

The skeleton has **24 joints**:

```
Pelvis (0)
├── Left_Hip (1) → Left_Knee (4) → Left_Ankle (7) → Left_Foot (10)
├── Right_Hip (2) → Right_Knee (5) → Right_Ankle (8) → Right_Foot (11)
└── Spine1 (3) → Spine2 (6) → Spine3 (9)
    ├── Neck (12) → Head (15)
    ├── Left_Collar (13) → Left_Shoulder (16) → Left_Elbow (18) → Left_Wrist (20) → Left_Hand (22)
    └── Right_Collar (14) → Right_Shoulder (17) → Right_Elbow (19) → Right_Wrist (21) → Right_Hand (23)
```

## Performance Impact

**Processing time:** ~10-15% slower than standard mesh rendering
- Standard rendering: 5-10 minutes
- With skeleton: 6-11 minutes

**Why?** Additional rendering passes for skeleton videos.

## Technical Details

### Joint Extraction

Joints are extracted from SMPL vertices using the J_regressor matrix:

```python
# Load J_regressor
J_regressor = torch.load("hmr4d/utils/body_model/smpl_neutral_J_regressor.pt")

# Get vertices from SMPL
smplx_out = smplx(**smpl_params)
vertices = smplx_out.vertices  # (frames, 6890, 3)

# Extract joints
joints = einsum(J_regressor, vertices, "j v, l v i -> l j i")  # (frames, 24, 3)
```

### 2D Projection

3D joints are projected to 2D using camera intrinsics:

```python
# Project to 2D
joints_2d = project_joints_to_2d(joints_3d, K)

# Projection formula: [u, v, d] = K @ [x, y, z]
# Normalize: [u/d, v/d]
```

### Skeleton Drawing

Uses OpenCV to draw:
- Circles for joints (radius 6px, green)
- Lines for bones (thickness 3px, dark green)

## Customization

You can modify visualization in `skeleton_renderer.py`:

```python
draw_smpl_skeleton_on_image(
    img,
    joints_2d,
    joint_color=(0, 255, 0),    # BGR: Green
    bone_color=(0, 200, 0),      # BGR: Dark green
    joint_radius=6,              # Pixel radius
    bone_thickness=3             # Line thickness
)
```

**Color options:**
- `(0, 255, 0)` - Green (default)
- `(255, 0, 0)` - Blue
- `(0, 0, 255)` - Red
- `(255, 255, 255)` - White

## Comparison: Mesh vs Skeleton

| Feature | Mesh Rendering | Skeleton Rendering |
|---------|---------------|-------------------|
| Visual detail | High (full body surface) | Low (joints/bones only) |
| File size | Larger | Smaller |
| Processing time | Faster | Slightly slower |
| Motion analysis | Harder to see joints | Easy to see joints |
| Animation use | Character rendering | Motion reference |
| Programmatic use | Complex (vertices) | Simple (24 points) |

## Integration Examples

### Blender (Python)

```python
import json
import bpy

# Load joints
with open('joints.json') as f:
    data = json.load(f)

joints_global = data['joints_global_space']  # (frames, 24, 3)

# Create armature
for frame_idx, frame_joints in enumerate(joints_global):
    bpy.context.scene.frame_set(frame_idx)

    for joint_idx, (x, y, z) in enumerate(frame_joints):
        # Set bone position
        bone = armature.bones[joint_idx]
        bone.head = (x, y, z)
        bone.keyframe_insert(data_path="head", frame=frame_idx)
```

### Unity (C#)

```csharp
using UnityEngine;
using System.Collections.Generic;

[System.Serializable]
public class JointData
{
    public int num_frames;
    public List<List<List<float>>> joints_global_space;
}

// Load and animate
string json = File.ReadAllText("joints.json");
JointData data = JsonUtility.FromJson<JointData>(json);

// Apply to skeleton
for (int frame = 0; frame < data.num_frames; frame++)
{
    for (int joint = 0; joint < 24; joint++)
    {
        Vector3 pos = new Vector3(
            data.joints_global_space[frame][joint][0],
            data.joints_global_space[frame][joint][1],
            data.joints_global_space[frame][joint][2]
        );
        bones[joint].position = pos;
    }
}
```

## Troubleshooting

**Skeleton not visible:**
- Check that `render_skeleton: true` was set in request
- Verify output directory contains `skeleton_*.mp4` files
- Check logs: `docker compose logs -f gvhmr`

**Import error in container:**
```
ModuleNotFoundError: No module named 'skeleton_renderer'
```
- Rebuild container: `docker compose up --build -d --remove-orphans`
- Files must be in `/app/web_app/` directory

**Joints appear off-screen:**
- This is normal if subject moves out of frame
- Joint projection only draws if within image bounds

**Skeleton videos not in ZIP:**
- Skeleton files ARE included in `/download_zip/` endpoint
- Check `skeleton_incam.mp4` and `skeleton_only.mp4` in results

## Files Modified

Implementation required changes to:
- `web_app/skeleton_renderer.py` - NEW: Core skeleton drawing utilities
- `web_app/render_skeleton.py` - NEW: Skeleton rendering functions
- `web_app/demo_with_skeleton.py` - NEW: Modified demo script
- `web_app/app.py` - Added `render_skeleton` parameter
- `web_app/templates/index.html` - Added checkbox for skeleton option
- `web_app/static/js/script.js` - Send skeleton flag to API

## References

- SMPL Model: https://smpl.is.tue.mpg.de/
- SMPL Joint Regressor: Uses neutral J_regressor (24 joints)
- OpenCV Drawing: https://docs.opencv.org/4.x/dc/da5/tutorial_py_drawing_functions.html
