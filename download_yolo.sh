#!/bin/bash

# Script to download YOLO model

set -e

echo "Downloading YOLOv8x model..."

mkdir -p models/yolo

cd models/yolo

if [ -f "yolov8x.pt" ]; then
    echo "YOLOv8x model already exists!"
else
    echo "Downloading from GitHub releases..."
    wget https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8x.pt
    echo "Download complete!"
fi

echo "YOLOv8x model is ready at: models/yolo/yolov8x.pt"
