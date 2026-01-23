# GVHMR Model Download Guide

## Quick Download Links

### GVHMR Checkpoints (Google Drive)

**Main checkpoint folder**: https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link

Download these files from the Google Drive link above:

1. **gvhmr_siga24_release.ckpt**
   - Location: Save to `models/gvhmr/`
   - Size: ~several GB
   - Purpose: Main GVHMR model trained for 420 epochs on 2x4090 GPUs

2. **epoch=10-step=25000.ckpt** (HMR2)
   - Location: Save to `models/hmr2/`
   - Purpose: Human mesh recovery model

3. **vitpose-h-multi-coco.pth** (ViTPose)
   - Location: Save to `models/vitpose/`
   - Purpose: 2D pose detection

### YOLO Model (Already Downloaded ✓)

- **yolov8x.pt** - Already downloaded via `download_yolo.sh`
- Location: `models/yolo/yolov8x.pt`
- Size: 131MB

### SMPL/SMPLX Body Models

**SMPL Models**:
1. Visit: https://smpl.is.tue.mpg.de/
2. Register for an account (free for research)
3. Download SMPL models (Python version)
4. Extract to `body_models/smpl/`

Required files in `body_models/smpl/`:
- `SMPL_MALE.pkl`
- `SMPL_FEMALE.pkl`
- `SMPL_NEUTRAL.pkl`

**SMPLX Models**:
1. Same registration at https://smpl.is.tue.mpg.de/
2. Download SMPLX models
3. Extract to `body_models/smplx/`

## Download Instructions

### Method 1: Manual Download (Recommended for large files)

1. **Download from Google Drive**:
   - Open https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD?usp=drive_link
   - Download each checkpoint file
   - Move to appropriate directory

2. **Download SMPL/SMPLX**:
   - Register at https://smpl.is.tue.mpg.de/
   - Download and extract models

### Method 2: Using gdown (for Google Drive)

Install gdown:
```bash
pip install gdown
```

Download files (replace FILE_ID with actual Google Drive file IDs):
```bash
# Example for gvhmr checkpoint
gdown https://drive.google.com/uc?id=FILE_ID -O models/gvhmr/gvhmr_siga24_release.ckpt
```

Note: For large files, you may need to use `gdown --fuzzy` or download manually.

## Verification

After downloading all files, run:

```bash
./check_readiness.sh
```

Expected output:
```
✓ models/yolo/yolov8x.pt
✓ models/gvhmr/gvhmr_siga24_release.ckpt
✓ models/hmr2/epoch=10-step=25000.ckpt
✓ models/vitpose/vitpose-h-multi-coco.pth
✓ SMPL models directory
✓ SMPLX models directory
```

## Directory Structure After Download

```
models/
├── gvhmr/
│   └── gvhmr_siga24_release.ckpt       [Download from Google Drive]
├── hmr2/
│   └── epoch=10-step=25000.ckpt        [Download from Google Drive]
├── vitpose/
│   └── vitpose-h-multi-coco.pth        [Download from Google Drive]
└── yolo/
    └── yolov8x.pt                      [✓ Already downloaded]

body_models/
├── smpl/
│   ├── SMPL_MALE.pkl                   [Download from SMPL website]
│   ├── SMPL_FEMALE.pkl                 [Download from SMPL website]
│   └── SMPL_NEUTRAL.pkl                [Download from SMPL website]
└── smplx/
    └── [SMPLX model files]             [Download from SMPL website]
```

## Important Notes

1. **Licensing**: By downloading these models, you agree to their respective licenses
2. **Storage**: Ensure you have at least 10GB free disk space
3. **Time**: Downloads may take 30-60 minutes depending on connection speed
4. **Authentication**: SMPL models require registration - this is normal and free

## Troubleshooting

### Google Drive quota exceeded
- Try downloading later
- Use a different Google account
- Download files one at a time

### SMPL registration issues
- Check spam folder for confirmation email
- Use academic email if possible
- Contact SMPL support if needed

### File permissions
After downloading, ensure files are readable:
```bash
chmod -R 644 models/
chmod -R 644 body_models/
```

## After Download

Once all models are downloaded:

1. Verify with `./check_readiness.sh`
2. Build container: `docker compose up --build -d`
3. Check logs: `docker compose logs -f`
4. Test at: http://localhost:5000

## References

- GVHMR GitHub: https://github.com/zju3dv/GVHMR
- GVHMR Models: https://drive.google.com/drive/folders/1eebJ13FUEXrKBawHpJroW0sNSxLjh9xD
- SMPL Website: https://smpl.is.tue.mpg.de/
- GVHMR Project Page: https://zju3dv.github.io/gvhmr/
- Paper: https://arxiv.org/html/2409.06662v1
