# Output Control and Naming Guide

## Current Output Files

### When `render_skeleton: false` (default)
```
results/VideoName/VideoName/
├── 0_input_video.mp4          # Copy of input video
├── 1_incam.mp4                 # Mesh overlay on input (in-camera view)
├── 2_global.mp4                # Mesh from global camera view
├── VideoName_3_incam_global_horiz.mp4  # Side-by-side comparison
├── hmr4d_results.pt            # SMPL parameters
└── preprocess/                 # Intermediate processing files
    ├── bbx.pt
    ├── vitpose.pt
    ├── vit_features.pt
    └── slam_results.pt (if moving camera)
```

### When `render_skeleton: true`
```
results/VideoName/VideoName/
├── 0_input_video.mp4
├── 1_incam.mp4
├── 2_global.mp4
├── VideoName_3_incam_global_horiz.mp4
├── skeleton_incam.mp4          # NEW: Skeleton overlay on input
├── skeleton_only.mp4           # NEW: Skeleton on black background
├── joints.json                 # NEW: Joint positions data
├── hmr4d_results.pt
└── preprocess/
```

## Naming Logic Analysis

### Problems
1. **Numbered prefixes** (0_, 1_, 2_) - Not descriptive
2. **Inconsistent naming** - Mesh uses numbers, skeleton uses descriptive names
3. **Redundant input copy** - `0_input_video.mp4` duplicates upload
4. **Nested directories** - `VideoName/VideoName/` is redundant
5. **No control** - All outputs generated regardless of need

### Proposed Improved Naming

```
results/VideoName/
├── input.mp4                   # Original (optional)
├── mesh_incam.mp4              # Mesh overlay in-camera view
├── mesh_global.mp4             # Mesh global view
├── mesh_comparison.mp4         # Side-by-side mesh views
├── skeleton_incam.mp4          # Skeleton overlay
├── skeleton_only.mp4           # Skeleton on black
├── skeleton_global.mp4         # (Future) Skeleton global view
├── joints.json                 # Joint data
├── smpl_params.pt              # SMPL parameters (renamed from hmr4d_results.pt)
└── intermediate/               # All preprocessing files
    ├── bbx.pt
    ├── vitpose.pt
    ├── vit_features.pt
    └── slam_results.pt
```

## Adding Selective Output Control

### Option 1: Simple Presets (Recommended)

**API Enhancement:**
```json
{
  "filename": "video.mp4",
  "static_camera": true,
  "output_preset": "skeleton_only"
}
```

**Available Presets:**
- `"full"` (default) - All mesh + skeleton outputs
- `"mesh_only"` - Only mesh renders (current default behavior)
- `"skeleton_only"` - Only skeleton renders
- `"minimal"` - Just SMPL params + joints.json (no videos)
- `"api_ready"` - Only JSON/PT files for programmatic use

### Option 2: Granular Control (Advanced)

**API Enhancement:**
```json
{
  "filename": "video.mp4",
  "static_camera": true,
  "outputs": {
    "mesh_incam": true,
    "mesh_global": false,
    "mesh_comparison": false,
    "skeleton_incam": true,
    "skeleton_only": true,
    "skeleton_global": false,
    "joints_json": true,
    "copy_input": false,
    "save_intermediate": false
  }
}
```

### Option 3: Web UI Enhancement

Add dropdown in HTML:
```html
<div class="settings">
    <label>
        <input type="checkbox" id="staticCamera" checked>
        Static Camera
    </label>

    <label for="outputPreset">Output Type:</label>
    <select id="outputPreset">
        <option value="mesh_only">Mesh Only (default)</option>
        <option value="skeleton_only">Skeleton Only</option>
        <option value="full">Full (Mesh + Skeleton)</option>
        <option value="minimal">Minimal (data only)</option>
    </select>
</div>
```

## Implementation Plan

### Phase 1: Fix Naming (Low Risk)
Change output filenames to be more descriptive without breaking existing code.

**Changes:**
- `0_input_video.mp4` → `input.mp4`
- `1_incam.mp4` → `mesh_incam.mp4`
- `2_global.mp4` → `mesh_global.mp4`
- `{name}_3_incam_global_horiz.mp4` → `mesh_comparison.mp4`
- `hmr4d_results.pt` → `smpl_params.pt` (keep symlink for compatibility)
- `preprocess/` → `intermediate/`

**Where to change:** Hydra config files in `/app/gvhmr/hmr4d/configs/`

### Phase 2: Add Preset System (Medium Risk)
Add preset parameter to skip unwanted rendering.

**Changes:**
1. Add `output_preset` parameter to Flask API
2. Pass preset to demo script via environment variable
3. Modify demo script to skip rendering based on preset
4. Update web UI with dropdown

### Phase 3: Add Granular Control (Optional)
Allow fine-grained control over each output file.

## Quick Fix for Current Naming

### Rename After Processing (No Rebuild)
```bash
# Create convenience script
cat > rename_outputs.sh << 'EOF'
#!/bin/bash
RESULT_DIR="$1"

if [ -d "$RESULT_DIR" ]; then
    cd "$RESULT_DIR"

    # Rename mesh outputs
    [ -f "0_input_video.mp4" ] && mv "0_input_video.mp4" "input.mp4"
    [ -f "1_incam.mp4" ] && mv "1_incam.mp4" "mesh_incam.mp4"
    [ -f "2_global.mp4" ] && mv "2_global.mp4" "mesh_global.mp4"

    # Rename comparison (find file with pattern)
    find . -maxdepth 1 -name "*_3_incam_global_horiz.mp4" -exec mv {} "mesh_comparison.mp4" \;

    # Rename SMPL params
    [ -f "hmr4d_results.pt" ] && mv "hmr4d_results.pt" "smpl_params.pt"

    # Rename preprocess dir
    [ -d "preprocess" ] && mv "preprocess" "intermediate"

    echo "Renamed outputs in $RESULT_DIR"
else
    echo "Usage: $0 <result_directory>"
fi
EOF

chmod +x rename_outputs.sh

# Use it
./rename_outputs.sh results/HumanMotionTest/HumanMotionTest/
```

## Environment Variables for Output Control

You can already control some outputs via command line flags:

```bash
# Skip all rendering (just get SMPL params)
python demo.py --video input.mp4 --skip-render

# Verbose mode (adds debug visualizations)
python demo.py --video input.mp4 --verbose
```

## Recommended Next Steps

**For immediate use:**
1. Accept current naming as-is
2. Use `render_skeleton` flag to control skeleton outputs
3. Delete unwanted files after processing

**For production:**
1. Implement preset system (mesh_only, skeleton_only, full, minimal)
2. Fix naming to be more descriptive
3. Add web UI dropdown for presets

**For advanced users:**
1. Expose all output options via API
2. Allow custom naming templates
3. Add cleanup option to remove intermediate files

## Example: Minimal Output API Call

For fastest processing with smallest output:

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{
    "filename": "video.mp4",
    "static_camera": true,
    "output_preset": "minimal"
  }' \
  http://localhost:5000/process
```

Would produce only:
- `smpl_params.pt` - SMPL parameters
- `joints.json` - Joint positions
- No video renders (saves 5-7 minutes processing time)

## File Size Comparison

Typical 74-frame video results:

| File | Size | Time to Generate |
|------|------|-----------------|
| input.mp4 | 2.1 MB | <1s (copy) |
| mesh_incam.mp4 | 1.8 MB | ~2 min |
| mesh_global.mp4 | 1.5 MB | ~2 min |
| mesh_comparison.mp4 | 3.3 MB | <1s (merge) |
| skeleton_incam.mp4 | 1.2 MB | ~1 min |
| skeleton_only.mp4 | 0.8 MB | ~1 min |
| joints.json | 145 KB | <1s |
| smpl_params.pt | 321 KB | 0s (already generated) |
| **Total** | **11.2 MB** | **~6-7 minutes** |

**Minimal preset** (just PT + JSON):
- Total: 466 KB
- Time: ~30 seconds (just SMPL inference, no rendering)

## Questions?

**Q: Can I get only skeleton outputs, no mesh?**
A: Set `output_preset: "skeleton_only"` (requires implementation)

**Q: How do I avoid the nested VideoName/VideoName directory?**
A: This is set in Hydra config. Change `output_root` parameter or modify config files.

**Q: Can I customize filenames?**
A: Not currently exposed in API. Would require Hydra config changes.

**Q: What if I only want joints.json?**
A: Use `output_preset: "minimal"` or manually delete unwanted video files.
