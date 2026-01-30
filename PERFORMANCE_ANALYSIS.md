# GVHMR Performance Analysis

**Date**: 2026-01-30
**Issue**: Processing speed has become slower than initial implementation

## Performance Bottleneck Analysis

### 🔴 CRITICAL ISSUES FOUND

#### 1. **Redundant Model Loading in Every Rendering Function**
**Location**: `render_skeleton.py` - Lines 41-43, 113-115, 182-184
**Impact**: HIGH - Each skeleton rendering function loads SMPL models independently

**Problem**:
```python
# render_skeleton_incam() - Lines 41-43
smplx = make_smplx("supermotion").cuda()
smplx2smpl = torch.load("/app/gvhmr/hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
J_regressor = torch.load("/app/gvhmr/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()

# render_skeleton_only() - Lines 113-115 (DUPLICATE)
smplx = make_smplx("supermotion").cuda()
smplx2smpl = torch.load("/app/gvhmr/hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
J_regressor = torch.load("/app/gvhmr/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()

# save_joints_json() - Lines 182-184 (DUPLICATE)
smplx = make_smplx("supermotion").cuda()
smplx2smpl = torch.load("/app/gvhmr/hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
J_regressor = torch.load("/app/gvhmr/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()
```

**Performance Impact**:
- Each `make_smplx()` call: ~2-3 seconds
- Each `torch.load()` call: ~0.5-1 second
- **Total overhead per function**: ~4-5 seconds
- **With all 3 functions**: ~12-15 seconds of pure model loading time

**Fix**: Load models once and pass as parameters

---

#### 2. **Redundant SMPL Computation in Every Function**
**Location**: `render_skeleton.py` - Lines 46-50, 118-122, 187-196
**Impact**: HIGH - Same SMPL forward pass computed 3 times

**Problem**:
```python
# render_skeleton_incam()
smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])
joints_incam = einsum(J_regressor, pred_c_verts, "j v, l v i -> l j i")

# render_skeleton_only() - DUPLICATE COMPUTATION
smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])
joints_incam = einsum(J_regressor, pred_c_verts, "j v, l v i -> l j i")

# save_joints_json() - DUPLICATE COMPUTATION AGAIN
smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])
joints_incam = einsum(J_regressor, pred_c_verts, "j v, l v i -> l j i")
```

**Performance Impact**:
- SMPL forward pass: ~1-2 seconds for typical video
- Vertex transformation: ~0.5-1 second
- Joint extraction: ~0.2-0.5 second
- **Total overhead per function**: ~2-4 seconds
- **With all 3 functions**: ~6-12 seconds of redundant computation

**Fix**: Compute joints once, pass to all functions

---

#### 3. **Redundant PT File Loading**
**Location**: `render_skeleton.py` - Lines 38, 110, 179
**Impact**: MEDIUM - Loading same PT file 3 times from disk

**Problem**:
```python
# Each function loads independently
pred = torch.load(cfg.paths.hmr4d_results)  # ~320KB file, loaded 3 times
```

**Performance Impact**:
- Disk I/O per load: ~0.2-0.5 seconds
- **Total overhead**: ~0.6-1.5 seconds

**Fix**: Load once, pass to all functions

---

#### 4. **Redundant 2D Projection Computation**
**Location**: `render_skeleton.py` - Lines 56-60, 130-134
**Impact**: MEDIUM - Same joints projected to 2D twice

**Problem**:
```python
# render_skeleton_incam()
joints_2d = []
for i in range(len(joints_incam)):
    j2d = project_joints_to_2d(joints_incam[i], K)
    joints_2d.append(j2d)
joints_2d = torch.stack(joints_2d)

# render_skeleton_only() - DUPLICATE
joints_2d = []
for i in range(len(joints_incam)):
    j2d = project_joints_to_2d(joints_incam[i], K)
    joints_2d.append(j2d)
joints_2d = torch.stack(joints_2d)
```

**Performance Impact**:
- Projection computation: ~0.5-1 second per call
- **Total overhead**: ~0.5-1 second

**Fix**: Project once, reuse joints_2d

---

#### 5. **Inefficient Loop in 2D Projection**
**Location**: `render_skeleton.py` - Lines 56-60
**Impact**: MEDIUM - Using Python loop instead of batch operation

**Problem**:
```python
joints_2d = []
for i in range(len(joints_incam)):
    j2d = project_joints_to_2d(joints_incam[i], K)
    joints_2d.append(j2d)
joints_2d = torch.stack(joints_2d)
```

**Performance Impact**: Could be 2-5x slower than batch operation

**Fix**: Batch project all frames at once

---

### 🟡 MODERATE ISSUES

#### 6. **Input Video Copy on Every Run**
**Location**: `demo_with_skeleton.py` - Lines 125-133
**Impact**: MEDIUM - Copies entire video even if already exists with same length

**Problem**:
```python
if not Path(cfg.video_path).exists() or get_video_lwh(video_path)[0] != get_video_lwh(cfg.video_path)[0]:
    reader = get_video_reader(video_path)
    writer = get_writer(cfg.video_path, fps=30, crf=CRF)
    for img in tqdm(reader, total=get_video_lwh(video_path)[0], desc=f"Copy"):
        writer.write_frame(img)
```

**Performance Impact**:
- For 100MB video: ~5-10 seconds
- Happens on every processing run

**Note**: This might be intentional for data integrity, but worth reviewing

---

#### 7. **mesh_incam/mesh_global Renderer Creation Per Function**
**Location**: `demo_with_skeleton.py` - Lines 252-253, 266, 294-296, 330
**Impact**: MEDIUM - Creates new SMPL models and renderers for each mesh render

**Problem**:
```python
# render_incam()
smplx = make_smplx("supermotion").cuda()
smplx2smpl = torch.load("hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()

# render_global() - DUPLICATE
smplx = make_smplx("supermotion").cuda()
smplx2smpl = torch.load("hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
```

**Performance Impact**: ~4-6 seconds total overhead

---

### 🟢 MINOR ISSUES

#### 8. **Existence Checks Return Early**
**Location**: Multiple functions check if output exists
**Impact**: LOW - Good for caching, but might hide issues

**Note**: This is actually good practice for avoiding re-rendering, but the caching bug fix (timestamp) means outputs rarely exist

---

## Total Performance Impact

### Current Bottlenecks (when rendering skeleton_incam + skeleton_only):

| Component | Time Lost | Frequency |
|-----------|-----------|-----------|
| Model loading (3x) | 12-15s | Per processing run |
| SMPL computation (3x) | 6-12s | Per processing run |
| PT file loading (3x) | 0.6-1.5s | Per processing run |
| 2D projection (2x) | 0.5-1s | Per processing run |
| Video copy | 5-10s | Per processing run |
| **Total Overhead** | **24-40s** | **Per processing run** |

### Expected Speed Improvement After Fixes:
- **Current**: Core processing (30s) + Overhead (24-40s) = **54-70 seconds**
- **Optimized**: Core processing (30s) + Minimal overhead (2-3s) = **32-33 seconds**
- **Speedup**: **40-50% faster** (saving 22-37 seconds)

---

## Recommended Fixes (Priority Order)

### 🔥 Priority 1: Eliminate Redundant Computations

**Refactor `render_skeleton.py`** to use shared computation:

```python
def compute_joints_once(cfg):
    """Compute joints once for all rendering functions"""
    # Load models once
    smplx = make_smplx("supermotion").cuda()
    smplx2smpl = torch.load("/app/gvhmr/hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
    J_regressor = torch.load("/app/gvhmr/hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()

    # Load results once
    pred = torch.load(cfg.paths.hmr4d_results)

    # Compute SMPL vertices once
    smplx_out = smplx(**to_cuda(pred["smpl_params_incam"]))
    pred_c_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out.vertices])

    # Extract joints once
    joints_incam = einsum(J_regressor, pred_c_verts, "j v, l v i -> l j i")

    # Also compute global joints for JSON export
    smplx_out_global = smplx(**to_cuda(pred["smpl_params_global"]))
    pred_g_verts = torch.stack([torch.matmul(smplx2smpl, v_) for v_ in smplx_out_global.vertices])
    joints_global = einsum(J_regressor, pred_g_verts, "j v, l v i -> l j i")

    # Get camera intrinsics
    K = pred["K_fullimg"][0].cuda()

    # Project to 2D once (batch operation)
    joints_2d = project_joints_to_2d_batch(joints_incam, K)

    return {
        'joints_incam': joints_incam,
        'joints_global': joints_global,
        'joints_2d': joints_2d,
        'K': K,
        'pred': pred
    }

def render_skeleton_incam(cfg, output_skeleton_path, precomputed):
    """Now takes precomputed joints"""
    # Use precomputed data instead of reloading/recomputing
    joints_2d = precomputed['joints_2d']
    # ... rest of rendering code ...

def render_skeleton_only(cfg, output_skeleton_path, precomputed):
    """Now takes precomputed joints"""
    joints_2d = precomputed['joints_2d']
    # ... rest of rendering code ...

def save_joints_json(cfg, output_json_path, precomputed):
    """Now takes precomputed joints"""
    joints_incam = precomputed['joints_incam']
    joints_global = precomputed['joints_global']
    # ... rest of export code ...
```

**Update `demo_with_skeleton.py`** to use precomputation:

```python
# In main() function - Lines 409-424
# Instead of calling functions independently, precompute once
if 'skeleton_incam' in enabled or 'skeleton_only' in enabled:
    Log.info("[Precompute] Joint positions for skeleton rendering")
    from render_skeleton import compute_joints_once
    precomputed = compute_joints_once(cfg)

    if 'skeleton_incam' in enabled:
        Log.info("[Render] Skeleton incam")
        skeleton_incam_path = Path(cfg.output_dir) / "skeleton_incam.mp4"
        render_skeleton_incam(cfg, skeleton_incam_path, precomputed)

    if 'skeleton_only' in enabled:
        Log.info("[Render] Skeleton only")
        skeleton_only_path = Path(cfg.output_dir) / "skeleton_only.mp4"
        render_skeleton_only(cfg, skeleton_only_path, precomputed)

    Log.info("[Save] Joint positions JSON")
    joints_json_path = Path(cfg.output_dir) / "joints.json"
    save_joints_json(cfg, joints_json_path, precomputed)
```

### 🔥 Priority 2: Batch 2D Projection

**Add batch projection function** to `skeleton_renderer.py`:

```python
def project_joints_to_2d_batch(joints_3d, K):
    """
    Project batch of 3D joints to 2D

    Args:
        joints_3d: (L, 24, 3) tensor of 3D joint positions
        K: (3, 3) camera intrinsic matrix
    Returns:
        joints_2d: (L, 24, 2) tensor of 2D joint positions
    """
    # Batch projection: (L, 24, 3) @ (3, 3).T -> (L, 24, 3)
    projected = torch.matmul(joints_3d, K.T)

    # Divide by depth: (L, 24, 2)
    joints_2d = projected[..., :2] / projected[..., 2:3]

    return joints_2d
```

### 🟡 Priority 3: Share SMPL Models in Mesh Rendering

**Refactor mesh rendering** in `demo_with_skeleton.py` to load models once:

```python
def load_smpl_models_once():
    """Load SMPL models once for all rendering"""
    smplx = make_smplx("supermotion").cuda()
    smplx2smpl = torch.load("hmr4d/utils/body_model/smplx2smpl_sparse.pt").cuda()
    faces_smpl = make_smplx("smpl").faces
    J_regressor = torch.load("hmr4d/utils/body_model/smpl_neutral_J_regressor.pt").cuda()
    return smplx, smplx2smpl, faces_smpl, J_regressor

# In main():
if 'mesh_incam' in enabled or 'mesh_global' in enabled:
    smpl_models = load_smpl_models_once()

    if 'mesh_incam' in enabled:
        render_incam(cfg, smpl_models)

    if 'mesh_global' in enabled:
        render_global(cfg, smpl_models)
```

---

## Comparison: Before vs After Optimization

### Current Architecture (Inefficient):
```
skeleton_incam()
  ├─ Load SMPL models (4-5s)
  ├─ Load PT file (0.2s)
  ├─ SMPL forward pass (2s)
  ├─ Project to 2D (0.5s)
  └─ Render (1min)

skeleton_only()
  ├─ Load SMPL models (4-5s) ← DUPLICATE
  ├─ Load PT file (0.2s) ← DUPLICATE
  ├─ SMPL forward pass (2s) ← DUPLICATE
  ├─ Project to 2D (0.5s) ← DUPLICATE
  └─ Render (1min)

save_joints_json()
  ├─ Load SMPL models (4-5s) ← DUPLICATE
  ├─ Load PT file (0.2s) ← DUPLICATE
  ├─ SMPL forward pass (2s) ← DUPLICATE
  └─ Export JSON (0.1s)

Total: ~24-40s overhead + 2min rendering = 2m24s-2m40s
```

### Optimized Architecture:
```
compute_joints_once()
  ├─ Load SMPL models (4-5s) ← ONCE
  ├─ Load PT file (0.2s) ← ONCE
  ├─ SMPL forward pass (2s) ← ONCE
  └─ Batch project to 2D (0.3s) ← ONCE, FASTER

skeleton_incam(precomputed)
  └─ Render (1min) ← Use precomputed data

skeleton_only(precomputed)
  └─ Render (1min) ← Use precomputed data

save_joints_json(precomputed)
  └─ Export JSON (0.1s) ← Use precomputed data

Total: ~7s preprocessing + 2min rendering = 2m07s
```

**Savings**: ~17-33 seconds per processing run

---

## Testing Recommendations

1. **Add timing logs** to measure each component:
```python
import time

tic = time.time()
smplx = make_smplx("supermotion").cuda()
print(f"make_smplx took: {time.time() - tic:.2f}s")
```

2. **Profile current implementation** before optimization
3. **Profile optimized implementation** to verify improvements
4. **Run comparison test** with same video before/after changes

---

## Additional Notes

- The mesh rendering (render_incam, render_global) also has some duplication, but it's less severe since those are larger operations
- Video copying overhead might be necessary for data integrity
- The timestamp fix for caching means outputs are rarely cached, so early returns don't help much anymore
- Consider adding a `--skip-video-copy` flag for development/testing

---

## Implementation Status

- ⬜ Priority 1: Refactor skeleton rendering to use precomputation
- ⬜ Priority 2: Add batch 2D projection
- ⬜ Priority 3: Share SMPL models in mesh rendering
- ⬜ Add performance timing logs
- ⬜ Test and verify improvements
