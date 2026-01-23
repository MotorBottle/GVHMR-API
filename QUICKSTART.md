# GVHMR Quick Start Guide

## Prerequisites Check

1. **Docker Engine v2** installed
   ```bash
   docker compose version
   ```

2. **NVIDIA GPU and nvidia-docker2** installed
   ```bash
   nvidia-smi
   docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
   ```

## Step-by-Step Setup

### 1. Setup Model Directories

Run the setup script:
```bash
./setup_models.sh
```

This creates the necessary directory structure.

### 2. Download Model Checkpoints

**Important**: You must download these models before the system will work.

#### GVHMR Model
1. Visit the [GVHMR repository](https://github.com/zju3dv/GVHMR)
2. Go to releases or follow their model download instructions
3. Download `gvhmr_siga24_release.ckpt`
4. Place in `models/gvhmr/gvhmr_siga24_release.ckpt`

#### HMR2 Model
1. Download `epoch=10-step=25000.ckpt` from GVHMR model links
2. Place in `models/hmr2/epoch=10-step=25000.ckpt`

#### ViTPose Model
1. Download `vitpose-h-multi-coco.pth`
2. Place in `models/vitpose/vitpose-h-multi-coco.pth`

#### YOLO Model
1. Download `yolov8x.pt` from [Ultralytics](https://github.com/ultralytics/assets/releases)
2. Place in `models/yolo/yolov8x.pt`

#### SMPL/SMPLX Body Models
1. Register at [SMPL website](https://smpl.is.tue.mpg.de/)
2. Download SMPL models
3. Extract to `body_models/smpl/`
4. Download SMPLX models
5. Extract to `body_models/smplx/`

### 3. Verify Model Files

Check that all models are in place:
```bash
./setup_models.sh
```

You should see all checkmarks (✓) for the required models.

### 4. Build and Start Container

```bash
docker compose up --build -d
```

This will:
- Build the Docker image (takes 10-20 minutes first time)
- Download GVHMR source code
- Install all dependencies
- Start the web interface

### 5. Monitor Build Progress

```bash
docker compose logs -f
```

Wait until you see:
```
* Running on http://0.0.0.0:5000
```

### 6. Access Web Interface

Open your browser:
```
http://localhost:5000
```

### 7. Test with Sample Video

1. In the web interface, click "Choose Video File"
2. Select `HumanMotionTest.m4v` from your workspace
3. Click "Upload Video"
4. Ensure "Static Camera" is checked
5. Click "Process Video"
6. Wait for processing (5-10 minutes for first run)
7. Download results when complete

## Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs

# Check GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Missing models error
- Verify all model files are in correct locations
- Check file names match exactly (case-sensitive)
- Re-run `./setup_models.sh` to verify

### GPU out of memory
- Close other GPU applications
- Use shorter/lower resolution videos
- Restart Docker daemon: `sudo systemctl restart docker`

### Processing timeout
- Edit `.env` and increase `PROCESSING_TIMEOUT_SECONDS`
- Rebuild: `docker compose up --build -d`

## Daily Usage

After initial setup:

```bash
# Start container
docker compose up -d

# Stop container
docker compose down

# View logs
docker compose logs -f

# Update after code changes
docker compose up --build -d --remove-orphans
```

## Expected Results

After processing, you should get:
- 3D human pose and shape parameters
- World-grounded motion trajectories
- SMPL format output files
- Visualization files (if enabled in GVHMR)

Results are saved in `results/` directory.
