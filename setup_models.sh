#!/bin/bash

# GVHMR Model Setup Script
# This script helps create the necessary directory structure for model checkpoints

set -e

echo "========================================="
echo "GVHMR Model Setup"
echo "========================================="
echo ""

# Create directories
echo "Creating directory structure..."
mkdir -p models/{gvhmr,hmr2,vitpose,yolo,dpvo}
mkdir -p body_models/{smpl,smplx}
mkdir -p results
mkdir -p uploads

echo "Directories created successfully!"
echo ""

echo "========================================="
echo "Next Steps:"
echo "========================================="
echo ""
echo "1. Download GVHMR model checkpoint:"
echo "   - Visit: https://github.com/zju3dv/GVHMR"
echo "   - Download: gvhmr_siga24_release.ckpt"
echo "   - Place in: models/gvhmr/"
echo ""
echo "2. Download HMR2 checkpoint:"
echo "   - Download: epoch=10-step=25000.ckpt"
echo "   - Place in: models/hmr2/"
echo ""
echo "3. Download ViTPose checkpoint:"
echo "   - Download: vitpose-h-multi-coco.pth"
echo "   - Place in: models/vitpose/"
echo ""
echo "4. Download YOLO model:"
echo "   - Download: yolov8x.pt from Ultralytics"
echo "   - Place in: models/yolo/"
echo ""
echo "5. Download SMPL/SMPLX body models:"
echo "   - Register at: https://smpl.is.tue.mpg.de/"
echo "   - Download SMPL models → place in: body_models/smpl/"
echo "   - Download SMPLX models → place in: body_models/smplx/"
echo ""
echo "6. After downloading all models, build the container:"
echo "   docker compose up --build -d"
echo ""
echo "========================================="

# Check if any models already exist
echo ""
echo "Checking for existing models..."
echo ""

check_file() {
    if [ -f "$1" ]; then
        echo "✓ Found: $1"
        return 0
    else
        echo "✗ Missing: $1"
        return 1
    fi
}

check_file "models/gvhmr/gvhmr_siga24_release.ckpt"
check_file "models/hmr2/epoch=10-step=25000.ckpt"
check_file "models/vitpose/vitpose-h-multi-coco.pth"
check_file "models/yolo/yolov8x.pt"

echo ""
echo "Body models directory:"
if [ -d "body_models/smpl" ] && [ "$(ls -A body_models/smpl)" ]; then
    echo "✓ SMPL models found in body_models/smpl/"
else
    echo "✗ SMPL models not found in body_models/smpl/"
fi

if [ -d "body_models/smplx" ] && [ "$(ls -A body_models/smplx)" ]; then
    echo "✓ SMPLX models found in body_models/smplx/"
else
    echo "✗ SMPLX models not found in body_models/smplx/"
fi

echo ""
echo "Setup script completed!"
