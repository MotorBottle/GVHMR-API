# GVHMR Docker Deployment

Docker deployment of [GVHMR (Gravity-View Human Motion Recovery)](https://github.com/zju3dv/GVHMR) with GPU acceleration and a web interface for testing.

## Features

- Docker containerized deployment with NVIDIA GPU support
- Web interface for video upload and processing
- Complete documentation integrated into the UI
- Support for static and moving camera videos
- Automatic model checkpoint management

## Prerequisites

- Docker Engine v2 (with `docker compose` support)
- NVIDIA GPU with CUDA support
- nvidia-docker2 installed and configured
- At least 10GB free disk space
- GPU with minimum 8GB VRAM (recommended)

### Installing nvidia-docker2

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

Test GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Setup

### 1. Download Model Checkpoints

Create the following directory structure:

```bash
mkdir -p models/{gvhmr,hmr2,vitpose,yolo,dpvo}
mkdir -p body_models/{smpl,smplx}
```

Download the required model checkpoints:

**GVHMR Model:**
- Download `gvhmr_siga24_release.ckpt` from [GVHMR releases](https://github.com/zju3dv/GVHMR)
- Place in `models/gvhmr/`

**HMR2 Model:**
- Download `epoch=10-step=25000.ckpt`
- Place in `models/hmr2/`

**ViTPose Model:**
- Download `vitpose-h-multi-coco.pth`
- Place in `models/vitpose/`

**YOLO Model:**
- Download `yolov8x.pt` from [Ultralytics](https://github.com/ultralytics/ultralytics)
- Place in `models/yolo/`

**SMPL/SMPLX Body Models:**
- Register and download from [SMPL website](https://smpl.is.tue.mpg.de/)
- Place SMPL models in `body_models/smpl/`
- Place SMPLX models in `body_models/smplx/`

### 2. Build and Run

```bash
# Build and start the container
docker compose up --build -d

# View logs
docker compose logs -f

# Stop the container
docker compose down

# Remove orphan images when updating
docker compose up --build -d --remove-orphans
```

### 3. Access Web Interface

Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. **Upload Video**: Select a video file (MP4, AVI, MOV, or MKV)
2. **Configure Settings**: Choose camera type (static or moving)
3. **Process**: Click "Process Video" and wait for completion
4. **Download Results**: View and download the processed motion data

### Testing with Sample Video

The repository includes a sample video `HumanMotionTest.m4v` for testing:

1. Open http://localhost:5000
2. Upload `HumanMotionTest.m4v`
3. Select "Static Camera" (recommended for faster processing)
4. Click "Process Video"
5. Wait for processing to complete (may take 5-10 minutes)
6. Download results from the web interface

## Project Structure

```
.
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── web_app/                    # Web interface
│   ├── app.py                  # Flask application
│   ├── templates/              # HTML templates
│   │   └── index.html
│   └── static/                 # CSS and JavaScript
│       ├── css/style.css
│       └── js/script.js
├── models/                     # Model checkpoints (not in git)
├── body_models/                # SMPL/SMPLX models (not in git)
├── results/                    # Processing results (not in git)
├── .env.example               # Environment configuration template
└── README.md                  # This file
```

## Configuration

Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

Available settings:
- `PORT`: Web interface port (default: 5000)
- `MAX_UPLOAD_SIZE_MB`: Maximum video file size (default: 500MB)
- `PROCESSING_TIMEOUT_SECONDS`: Processing timeout (default: 600s)

## Troubleshooting

### GPU not detected
```bash
# Check NVIDIA driver
nvidia-smi

# Check docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Restart docker
sudo systemctl restart docker
```

### Out of memory errors
- Reduce video resolution or length
- Close other GPU-intensive applications
- Ensure GPU has at least 8GB VRAM

### Missing model checkpoints
- Check that all models are downloaded to the correct directories
- Verify file permissions
- Rebuild the container: `docker compose up --build -d`

### Processing timeout
- Increase `PROCESSING_TIMEOUT_SECONDS` in `.env`
- Use static camera mode for faster processing
- Process shorter video clips

## Development

### View container logs
```bash
docker compose logs -f gvhmr
```

### Execute commands in container
```bash
docker compose exec gvhmr bash
```

### Rebuild after code changes
```bash
docker compose up --build -d --remove-orphans
```

## Technical Details

- **Base Image**: nvidia/cuda:12.1.0-devel-ubuntu22.04
- **Python Version**: 3.10
- **PyTorch Version**: 2.3.0 with CUDA 12.1
- **Web Framework**: Flask
- **GPU Requirements**: NVIDIA GPU with CUDA support

## License

This deployment follows the license of the original [GVHMR repository](https://github.com/zju3dv/GVHMR).

## Citation

If you use GVHMR in your research, please cite:

```bibtex
@article{gvhmr2024,
  title={GVHMR: World-Grounded Human Motion Recovery via Gravity-View Coordinates},
  author={[Authors]},
  journal={SIGGRAPH Asia},
  year={2024}
}
```

## Support

- GVHMR Repository: https://github.com/zju3dv/GVHMR
- Issues: Report issues specific to this Docker deployment in this repository
