#!/bin/bash

# GVHMR Deployment Readiness Checker

echo "========================================="
echo "GVHMR Deployment Readiness Check"
echo "========================================="
echo ""

READY=true

# Check Docker
echo "[1/6] Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✓ Docker installed"
    if docker compose version &> /dev/null; then
        echo "✓ Docker Compose v2 available"
    else
        echo "✗ Docker Compose v2 not available"
        echo "  Please install Docker Compose v2"
        READY=false
    fi
else
    echo "✗ Docker not installed"
    READY=false
fi
echo ""

# Check NVIDIA GPU
echo "[2/6] Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo "✓ NVIDIA driver installed"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "✗ NVIDIA driver not found"
    READY=false
fi
echo ""

# Check nvidia-docker
echo "[3/6] Checking nvidia-docker..."
if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "✓ nvidia-docker2 working"
else
    echo "✗ nvidia-docker2 not configured properly"
    echo "  Run: sudo apt-get install nvidia-docker2"
    echo "  Then: sudo systemctl restart docker"
    READY=false
fi
echo ""

# Check model files
echo "[4/6] Checking model files..."
check_model() {
    if [ -f "$1" ]; then
        echo "✓ $1"
        return 0
    else
        echo "✗ $1 (missing)"
        return 1
    fi
}

check_model "models/yolo/yolov8x.pt"
if ! check_model "models/gvhmr/gvhmr_siga24_release.ckpt"; then READY=false; fi
if ! check_model "models/hmr2/epoch=10-step=25000.ckpt"; then READY=false; fi
if ! check_model "models/vitpose/vitpose-h-multi-coco.pth"; then READY=false; fi
echo ""

# Check body models
echo "[5/6] Checking body models..."
if [ -d "body_models/smpl" ] && [ "$(ls -A body_models/smpl 2>/dev/null)" ]; then
    echo "✓ SMPL models directory ($(ls -1 body_models/smpl | wc -l) files)"
else
    echo "✗ SMPL models missing"
    READY=false
fi

if [ -d "body_models/smplx" ] && [ "$(ls -A body_models/smplx 2>/dev/null)" ]; then
    echo "✓ SMPLX models directory ($(ls -1 body_models/smplx | wc -l) files)"
else
    echo "✗ SMPLX models missing"
    READY=false
fi
echo ""

# Check test video
echo "[6/6] Checking test video..."
if [ -f "HumanMotionTest.m4v" ]; then
    SIZE=$(du -h HumanMotionTest.m4v | cut -f1)
    echo "✓ Test video present ($SIZE)"
else
    echo "⚠ Test video not found (optional)"
fi
echo ""

# Summary
echo "========================================="
echo "Summary"
echo "========================================="
if [ "$READY" = true ]; then
    echo "✅ System is READY for deployment!"
    echo ""
    echo "Next steps:"
    echo "1. docker compose up --build -d"
    echo "2. docker compose logs -f"
    echo "3. Open http://localhost:5000"
    echo "4. Upload and process HumanMotionTest.m4v"
else
    echo "❌ System is NOT ready"
    echo ""
    echo "Please address the issues above."
    echo ""
    echo "For model downloads, see:"
    echo "- NEXT_STEPS.md"
    echo "- QUICKSTART.md"
fi
echo "========================================="

exit 0
