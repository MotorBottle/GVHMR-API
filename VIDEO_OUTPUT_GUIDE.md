# Video Output Control Guide

## Overview

You now have full control over which videos are generated and improved naming for all output files.

## Better Video Naming

**Old naming** (numbered prefixes):
```
0_input_video.mp4
1_incam.mp4
2_global.mp4
VideoName_3_incam_global_horiz.mp4
```

**New naming** (descriptive):
```
input.mp4
mesh_incam.mp4
mesh_global.mp4
mesh_comparison.mp4
skeleton_incam.mp4
skeleton_only.mp4
joints.json
```

**PT files** (unchanged):
```
hmr4d_results.pt
preprocess/bbx.pt
preprocess/vitpose.pt
preprocess/vit_features.pt
preprocess/slam_results.pt
```

## Command Line Usage

### Basic Examples

**All videos** (default):
```bash
python demo_with_skeleton.py --video input.mp4 --output_root results/ -s
```

**No videos** (PT files only, fastest):
```bash
python demo_with_skeleton.py --video input.mp4 --output_root results/ \
  -s --video_render=false
```

**Only skeleton videos**:
```bash
python demo_with_skeleton.py --video input.mp4 --output_root results/ \
  -s --video_type=skeleton_incam,skeleton_only
```

**Only mesh incam**:
```bash
python demo_with_skeleton.py --video input.mp4 --output_root results/ \
  -s --video_type=mesh_incam
```

### Parameters

**`--video_render`** (true/false)
- `true` (default): Generate videos
- `false`: Skip all video rendering, only generate PT files
- Saves 5-7 minutes processing time

**`--video_type`** (comma-separated list or 'all')
- `all` (default): Generate all video types
- Specific types:
  - `mesh_incam` - Mesh overlay on input video
  - `mesh_global` - Mesh from global camera view
  - `mesh_comparison` - Side-by-side mesh comparison
  - `skeleton_incam` - Skeleton overlay on input video
  - `skeleton_only` - Skeleton on black background

**Examples**:
```bash
--video_type=all                    # All videos
--video_type=mesh_incam             # Just one type
--video_type=mesh_incam,mesh_global # Multiple types
--video_type=skeleton_incam,skeleton_only  # Just skeleton
```

## API Usage

### REST API Examples

**1. All videos (default)**:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "static_camera": true,
    "render_skeleton": true
  }' \
  http://localhost:5000/process
```

**2. No videos (fastest, PT files only)**:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "static_camera": true,
    "render_skeleton": true,
    "video_render": false
  }' \
  http://localhost:5000/process
```

**3. Only skeleton videos**:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "static_camera": true,
    "render_skeleton": true,
    "video_type": "skeleton_incam,skeleton_only"
  }' \
  http://localhost:5000/process
```

**4. Only mesh incam**:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "static_camera": true,
    "render_skeleton": false,
    "video_type": "mesh_incam"
  }' \
  http://localhost:5000/process
```

### API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filename` | string | required | Uploaded video filename |
| `static_camera` | boolean | `true` | Use static camera mode |
| `render_skeleton` | boolean | `false` | Use skeleton demo (enables video control) |
| `video_render` | boolean | `true` | Enable video rendering |
| `video_type` | string | `"all"` | Comma-separated list of video types |

## Output File Reference

### Video Files

| Filename | Description | Size (74 frames) | Render Time |
|----------|-------------|------------------|-------------|
| `input.mp4` | Copy of input video | ~2 MB | <1s |
| `mesh_incam.mp4` | Mesh overlay on input | ~2 MB | ~2 min |
| `mesh_global.mp4` | Mesh global view | ~2 MB | ~2 min |
| `mesh_comparison.mp4` | Side-by-side comparison | ~3 MB | <1s |
| `skeleton_incam.mp4` | Skeleton overlay | ~1 MB | ~1 min |
| `skeleton_only.mp4` | Skeleton on black | ~800 KB | ~1 min |

### Data Files

| Filename | Description | Size | Always Generated |
|----------|-------------|------|------------------|
| `hmr4d_results.pt` | SMPL parameters | ~320 KB | Yes |
| `joints.json` | Joint positions (if skeleton) | ~150 KB | With skeleton |
| `preprocess/bbx.pt` | Bounding boxes | ~3 KB | Yes |
| `preprocess/vitpose.pt` | 2D keypoints | ~16 KB | Yes |
| `preprocess/vit_features.pt` | Features | ~300 KB | Yes |
| `preprocess/slam_results.pt` | Camera poses | ~15 KB | Moving camera |

## Performance Optimization

### Processing Time Comparison

**All videos** (default):
- Total time: ~6-7 minutes
- SMPL inference: ~30s
- Rendering: ~6 minutes

**No videos** (`--video_render=false`):
- Total time: ~30 seconds
- SMPL inference: ~30s
- Rendering: 0s
- **90% faster!**

**Skeleton only**:
- Total time: ~2-3 minutes
- SMPL inference: ~30s
- Skeleton rendering: ~2 minutes
- **60% faster than all videos**

**Mesh incam only**:
- Total time: ~2.5 minutes
- SMPL inference: ~30s
- Mesh rendering: ~2 minutes

### Recommended Use Cases

**Development/Testing**:
```bash
--video_render=false  # Get PT files instantly
```

**API/Programmatic Use**:
```bash
--video_type=skeleton_only  # Lightweight visualization
```

**Full Analysis**:
```bash
--video_type=all  # Everything
```

**Quick Preview**:
```bash
--video_type=mesh_incam  # Just overlay
```

## Web Interface

Currently the web interface uses default settings (`render_skeleton` checkbox).

To add video type selection to web UI, you would need:

1. Add dropdown in `templates/index.html`:
```html
<select id="videoType">
  <option value="all">All Videos</option>
  <option value="mesh_incam">Mesh Incam Only</option>
  <option value="skeleton_incam,skeleton_only">Skeleton Only</option>
  <option value="none">No Videos (PT only)</option>
</select>
```

2. Update `static/js/script.js`:
```javascript
const videoType = document.getElementById('videoType').value;
const requestData = {
  filename: uploadedFilename,
  static_camera: staticCameraCheckbox.checked,
  render_skeleton: renderSkeletonCheckbox.checked,
  video_render: videoType !== 'none',
  video_type: videoType === 'none' ? '' : videoType
};
```

## Migration from Old Naming

If you have existing results with old naming, use this script:

```bash
#!/bin/bash
# rename_old_outputs.sh
RESULT_DIR="$1"

cd "$RESULT_DIR" || exit

# Rename videos
[ -f "0_input_video.mp4" ] && mv "0_input_video.mp4" "input.mp4"
[ -f "1_incam.mp4" ] && mv "1_incam.mp4" "mesh_incam.mp4"
[ -f "2_global.mp4" ] && mv "2_global.mp4" "mesh_global.mp4"

# Find and rename comparison video
find . -maxdepth 1 -name "*_3_incam_global_horiz.mp4" \
  -exec mv {} "mesh_comparison.mp4" \;

echo "Renamed videos in $RESULT_DIR"
```

Usage:
```bash
chmod +x rename_old_outputs.sh
./rename_old_outputs.sh results/VideoName/VideoName/
```

## Examples by Use Case

### Research (Need all data)
```bash
python demo_with_skeleton.py --video input.mp4 -s --video_type=all
```
Output: All videos + PT files (~11 MB, 6-7 min)

### Animation (Need skeleton)
```bash
python demo_with_skeleton.py --video input.mp4 -s \
  --video_type=skeleton_incam,skeleton_only
```
Output: Skeleton videos + joints.json (~2 MB, 2 min)

### ML Training (Need parameters only)
```bash
python demo_with_skeleton.py --video input.mp4 -s --video_render=false
```
Output: Just hmr4d_results.pt (~320 KB, 30s)

### Quick Visualization
```bash
python demo_with_skeleton.py --video input.mp4 -s --video_type=mesh_incam
```
Output: One overlay video (~2 MB, 2.5 min)

## Troubleshooting

**Q: Video not generated but no error?**
A: Check if the video type is in your `--video_type` list

**Q: Comparison video missing?**
A: Need both `mesh_incam` and `mesh_global` in video_type

**Q: Joints.json not generated?**
A: Only created when skeleton videos are requested

**Q: Old numbered files still appear?**
A: Only new runs use new naming. Rename old files with migration script above

**Q: How to get PT files without waiting for videos?**
A: Use `--video_render=false` for instant results

## Complete Example

```bash
# Upload
curl -X POST -F "video=@test.mp4" http://localhost:5000/upload

# Process with selective output
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "filename": "test.mp4",
    "static_camera": true,
    "render_skeleton": true,
    "video_type": "skeleton_incam,mesh_incam"
  }' \
  http://localhost:5000/process

# Download
curl -O -J http://localhost:5000/download_zip/test
```

Result ZIP contains:
- `skeleton_incam.mp4`
- `mesh_incam.mp4`
- `joints.json`
- `hmr4d_results.pt`
- `preprocess/` (all PT files)
