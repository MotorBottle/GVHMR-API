FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    python3-tk \
    git \
    wget \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set python3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Set working directory
WORKDIR /app

# Clone GVHMR repository
RUN git clone https://github.com/zju3dv/GVHMR.git /app/gvhmr

WORKDIR /app/gvhmr

# Install PyTorch with CUDA 12.1 support first
RUN pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cu121

# Install fvcore (required for pytorch3d)
RUN pip install fvcore iopath

# Install pytorch3d
RUN pip install --no-index --no-cache-dir pytorch3d -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu121_pyt230/download.html

# Install chumpy separately (has build issues with newer pip)
RUN pip install chumpy --no-build-isolation

# Install GVHMR requirements
RUN pip install -r requirements.txt

# Install GVHMR package
RUN pip install -e .

# Create necessary directories
RUN mkdir -p inputs/checkpoints/gvhmr \
    inputs/checkpoints/hmr2 \
    inputs/checkpoints/vitpose \
    inputs/checkpoints/yolo \
    inputs/checkpoints/dpvo \
    inputs/body_models/smpl \
    inputs/body_models/smplx \
    outputs/demo \
    uploads \
    results

# Copy web interface
COPY web_app /app/web_app
WORKDIR /app/web_app

# Install Flask and additional dependencies
RUN pip install flask flask-cors python-dotenv pillow

# Expose port for web interface
EXPOSE 5000

# Set environment variables
ENV CUDA_HOME=/usr/local/cuda-12.1
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Run web application
CMD ["python", "app.py"]
