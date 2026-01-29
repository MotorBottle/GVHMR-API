# GVHMR API Usage Guide

Quick reference for developers integrating with the GVHMR service via HTTP requests.

## Base URL

```
http://localhost:5000
```

(Replace with your deployment URL/port)

## API Workflow

```
1. Upload video → 2. Process video → 3. Download results (ZIP or individual files)
```

## Endpoints

### 1. Health Check

**GET** `/health`

Check service status and model availability.

```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "models_installed": {
    "GVHMR": true,
    "HMR2": true,
    "ViTPose": true,
    "YOLO": true,
    "DPVO (optional)": true
  }
}
```

---

### 2. Upload Video

**POST** `/upload`

Upload a video file for processing.

**Content-Type:** `multipart/form-data`

**Parameters:**
- `video` (file): Video file (MP4, AVI, MOV, MKV, M4V)
- Max size: 500MB

**Example:**
```bash
curl -X POST \
  -F "video=@/path/to/video.mp4" \
  http://localhost:5000/upload
```

**Success Response (200):**
```json
{
  "message": "File uploaded successfully",
  "filename": "video.mp4"
}
```

**Error Response (400/413):**
```json
{
  "error": "File too large. Maximum size is 500MB"
}
```

---

### 3. Process Video

**POST** `/process`

Process an uploaded video to extract human motion.

**Content-Type:** `application/json`

**Body:**
```json
{
  "filename": "video.mp4",
  "static_camera": true,
  "render_skeleton": false,
  "video_render": true,
  "video_type": "all"
}
```

**Parameters:**
- `filename` (string, required): Name returned from upload endpoint
- `static_camera` (boolean, optional):
  - `true`: Use static camera mode (faster, no DPVO required)
  - `false`: Use moving camera mode (requires DPVO model)
  - Default: `true`
- `render_skeleton` (boolean, optional):
  - `true`: Use skeleton demo (enables skeleton visualization and video control)
  - `false`: Use standard mesh demo
  - Default: `false`
- `video_render` (boolean, optional):
  - `true`: Generate videos
  - `false`: Skip all video rendering, only generate PT files (90% faster)
  - Default: `true`
  - **Note**: Only works when `render_skeleton: true`
- `video_type` (string, optional):
  - `"all"`: Generate all video types
  - Comma-separated list of specific types:
    - `"mesh_incam"` - Mesh overlay on input video
    - `"mesh_global"` - Mesh from global camera view
    - `"mesh_comparison"` - Side-by-side mesh comparison
    - `"skeleton_incam"` - Skeleton overlay on input video
    - `"skeleton_only"` - Skeleton on black background
  - Default: `"all"`
  - **Note**: Only works when `render_skeleton: true`

**Examples:**

**Basic processing (mesh only):**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename":"video.mp4","static_camera":true}' \
  http://localhost:5000/process
```

**Skeleton visualization:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename":"video.mp4","static_camera":true,"render_skeleton":true}' \
  http://localhost:5000/process
```

**Fast processing (PT files only, no videos):**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename":"video.mp4","static_camera":true,"render_skeleton":true,"video_render":false}' \
  http://localhost:5000/process
```

**Selective video output (only skeleton videos):**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename":"video.mp4","static_camera":true,"render_skeleton":true,"video_type":"skeleton_incam,skeleton_only"}' \
  http://localhost:5000/process
```

**Single video type (mesh incam only):**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename":"video.mp4","static_camera":true,"render_skeleton":true,"video_type":"mesh_incam"}' \
  http://localhost:5000/process
```

**Success Response (200):**
```json
{
  "message": "Video processed successfully",
  "output_path": "video"
}
```

**Notes:**
- Processing takes 5-10 minutes depending on video length
- `output_path` is used for downloading results
- This is a **blocking request** - response returns when processing completes

**Error Response (500):**
```json
{
  "error": "Missing model checkpoints",
  "missing_models": ["DPVO (optional)"],
  "message": "Please download the required model checkpoints. See documentation."
}
```

---

## Video Output Control

### Overview

When using `render_skeleton: true`, you get full control over video generation with improved naming.

### Better File Naming

**Old naming** (standard demo):
- `0_input_video.mp4`, `1_incam.mp4`, `2_global.mp4`

**New naming** (skeleton demo):
- `input.mp4`, `mesh_incam.mp4`, `mesh_global.mp4`, `skeleton_incam.mp4`, etc.

PT files keep original names (`hmr4d_results.pt`, `preprocess/*.pt`)

### Video Control Parameters

**Skip all videos** (fastest, PT files only):
```json
{
  "filename": "video.mp4",
  "static_camera": true,
  "render_skeleton": true,
  "video_render": false
}
```
→ Result: Only PT files, ~30 seconds (90% faster)

**Generate specific videos only:**
```json
{
  "filename": "video.mp4",
  "static_camera": true,
  "render_skeleton": true,
  "video_type": "skeleton_incam,mesh_incam"
}
```
→ Result: Only skeleton overlay + mesh overlay, ~3 minutes

**All videos** (default):
```json
{
  "filename": "video.mp4",
  "static_camera": true,
  "render_skeleton": true,
  "video_type": "all"
}
```
→ Result: All 5 video types, ~6-7 minutes

### Available Video Types

| Type | Description | Size | Time |
|------|-------------|------|------|
| `mesh_incam` | Mesh overlay on input | ~2MB | ~2min |
| `mesh_global` | Mesh global view | ~2MB | ~2min |
| `mesh_comparison` | Side-by-side comparison | ~3MB | <1s |
| `skeleton_incam` | Skeleton overlay | ~1MB | ~1min |
| `skeleton_only` | Skeleton on black | ~800KB | ~1min |

### Use Cases

**Development/Testing:**
- Use `video_render: false` for instant PT file generation

**API/Programmatic:**
- Use `video_type: "skeleton_only"` for lightweight visualization

**Full Analysis:**
- Use `video_type: "all"` for complete output

**Quick Preview:**
- Use `video_type: "mesh_incam"` for single overlay

See [VIDEO_OUTPUT_GUIDE.md](VIDEO_OUTPUT_GUIDE.md) for comprehensive documentation.

---

### 4. Download Results (ZIP)

**GET** `/download_zip/<output_path>`

Download all results as a single ZIP file.

**Example:**
```bash
curl -O -J http://localhost:5000/download_zip/video
```

**Response:**
- Binary ZIP file
- Filename: `{output_path}_results.zip`
- Contains: All PT files, renders, and other outputs

---

### 5. Download Individual Files

**GET** `/download/<output_path>/<filename>`

Download a specific result file.

**Example:**
```bash
curl -O http://localhost:5000/download/video/hmr4d_results.pt
```

---

### 6. List Results

**GET** `/results/<output_path>`

Get list of available result files.

**Example:**
```bash
curl http://localhost:5000/results/video
```

**Response:**
```json
{
  "files": [
    "hmr4d_results.pt",
    "preprocess/vitpose.pt",
    "preprocess/vit_features.pt",
    "render.mp4"
  ]
}
```

---

## Complete Workflow Example

### Bash Script

```bash
#!/bin/bash

VIDEO_FILE="sample.mp4"
API_URL="http://localhost:5000"

# 1. Upload video
echo "Uploading video..."
UPLOAD_RESPONSE=$(curl -s -X POST -F "video=@${VIDEO_FILE}" ${API_URL}/upload)
FILENAME=$(echo $UPLOAD_RESPONSE | jq -r '.filename')

if [ "$FILENAME" == "null" ]; then
    echo "Upload failed: $UPLOAD_RESPONSE"
    exit 1
fi

echo "Uploaded: $FILENAME"

# 2. Process video (this will take several minutes)
echo "Processing video... (this may take 5-10 minutes)"
PROCESS_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"filename\":\"${FILENAME}\",\"static_camera\":true}" \
    ${API_URL}/process)

OUTPUT_PATH=$(echo $PROCESS_RESPONSE | jq -r '.output_path')

if [ "$OUTPUT_PATH" == "null" ]; then
    echo "Processing failed: $PROCESS_RESPONSE"
    exit 1
fi

echo "Processing complete: $OUTPUT_PATH"

# 3. Download results as ZIP
echo "Downloading results..."
curl -O -J ${API_URL}/download_zip/${OUTPUT_PATH}

echo "Done! Results saved to ${OUTPUT_PATH}_results.zip"
```

### Python Example

```python
import requests
import time

API_URL = "http://localhost:5000"

# 1. Upload video
with open("sample.mp4", "rb") as f:
    response = requests.post(
        f"{API_URL}/upload",
        files={"video": f}
    )

upload_data = response.json()
filename = upload_data["filename"]
print(f"Uploaded: {filename}")

# 2. Process video (with video control)
print("Processing video... (this may take 5-10 minutes)")
response = requests.post(
    f"{API_URL}/process",
    json={
        "filename": filename,
        "static_camera": True,
        "render_skeleton": True,
        "video_type": "skeleton_incam,mesh_incam"  # Only 2 videos instead of all
    }
)

process_data = response.json()
output_path = process_data["output_path"]
print(f"Processing complete: {output_path}")

# 3. Download results as ZIP
response = requests.get(f"{API_URL}/download_zip/{output_path}")

zip_filename = f"{output_path}_results.zip"
with open(zip_filename, "wb") as f:
    f.write(response.content)

print(f"Results saved to {zip_filename}")
```

### JavaScript/Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const API_URL = 'http://localhost:5000';

async function processVideo(videoPath) {
    // 1. Upload video
    const formData = new FormData();
    formData.append('video', fs.createReadStream(videoPath));

    const uploadResponse = await axios.post(`${API_URL}/upload`, formData, {
        headers: formData.getHeaders()
    });

    const filename = uploadResponse.data.filename;
    console.log(`Uploaded: ${filename}`);

    // 2. Process video (with video control)
    console.log('Processing video... (this may take 5-10 minutes)');
    const processResponse = await axios.post(`${API_URL}/process`, {
        filename: filename,
        static_camera: true,
        render_skeleton: true,
        video_type: 'skeleton_incam,mesh_incam'  // Only 2 videos instead of all
    });

    const outputPath = processResponse.data.output_path;
    console.log(`Processing complete: ${outputPath}`);

    // 3. Download results as ZIP
    const zipResponse = await axios.get(
        `${API_URL}/download_zip/${outputPath}`,
        { responseType: 'arraybuffer' }
    );

    const zipFilename = `${outputPath}_results.zip`;
    fs.writeFileSync(zipFilename, zipResponse.data);
    console.log(`Results saved to ${zipFilename}`);
}

processVideo('sample.mp4');
```

---

## Result Files

### Standard Files (Always Generated)

**Data Files:**
- `hmr4d_results.pt` - Main SMPL parameters (body pose, shape, translation) ~320KB
- `preprocess/bbx.pt` - Bounding boxes ~3KB
- `preprocess/vitpose.pt` - 2D keypoint detections ~16KB
- `preprocess/vit_features.pt` - Deep learning features ~300KB
- `preprocess/slam_results.pt` - Camera poses (only for moving camera) ~15KB

### Video Files (Generated Based on Parameters)

**With `render_skeleton: false` (default, mesh only):**
- `0_input_video.mp4` - Copy of input video
- `1_incam.mp4` - Mesh overlay on input (in-camera view)
- `2_global.mp4` - Mesh from global camera view
- `{name}_3_incam_global_horiz.mp4` - Side-by-side comparison

**With `render_skeleton: true` (skeleton demo with new naming):**

All videos use descriptive names:
- `input.mp4` - Copy of input video
- `mesh_incam.mp4` - Mesh overlay on input video
- `mesh_global.mp4` - Mesh from global camera view
- `mesh_comparison.mp4` - Side-by-side mesh comparison
- `skeleton_incam.mp4` - Skeleton overlay on input video
- `skeleton_only.mp4` - Skeleton on black background
- `joints.json` - Joint positions in JSON format ~150KB

**Video Control:**
- Use `video_render: false` to skip all videos (only PT files, 90% faster)
- Use `video_type` to select specific videos (e.g., `"skeleton_incam,mesh_incam"`)

### File Sizes (74-frame example)

| File Type | Size | Time to Generate |
|-----------|------|------------------|
| PT files (all) | ~650KB | ~30s |
| input.mp4 | ~2MB | <1s (copy) |
| mesh_incam.mp4 | ~2MB | ~2min |
| mesh_global.mp4 | ~2MB | ~2min |
| mesh_comparison.mp4 | ~3MB | <1s (merge) |
| skeleton_incam.mp4 | ~1MB | ~1min |
| skeleton_only.mp4 | ~800KB | ~1min |
| joints.json | ~150KB | <1s |

**Performance:**
- All videos: ~6-7 minutes
- PT files only (`video_render: false`): ~30 seconds

See [VIDEO_OUTPUT_GUIDE.md](VIDEO_OUTPUT_GUIDE.md) for complete documentation on video control.

---

## Error Handling

**Common Errors:**

| Status | Error | Solution |
|--------|-------|----------|
| 400 | No file selected | Include `video` in form data |
| 400 | File type not allowed | Use MP4, AVI, MOV, MKV, or M4V |
| 413 | File too large | Video must be under 500MB |
| 500 | Missing model checkpoints | Download required models (see [MODEL_DOWNLOAD_GUIDE.md](MODEL_DOWNLOAD_GUIDE.md)) |
| 500 | Processing failed | Check logs: `docker compose logs -f` |

---

## Performance Notes

- **Processing time**:
  - PT files only (`video_render: false`): ~30 seconds (90% faster)
  - Selective videos: 1-3 minutes depending on types
  - All videos: 5-10 minutes per video (depends on length and GPU)
- **Concurrent requests**: Process one video at a time (no queue system currently)
- **Timeout**: Set client timeout to 15+ minutes for long videos (or 2 minutes for PT-only)
- **GPU memory**: ~8GB VRAM recommended
- **Optimization tip**: Use `render_skeleton: true` with `video_render: false` for fastest processing during development

---

## Development Tips

1. **Health check first**: Always verify models are loaded before processing
2. **Static camera mode**: Use `static_camera: true` if camera doesn't move (faster, no DPVO needed)
3. **Error logging**: Check container logs for detailed error messages
4. **File cleanup**: Uploaded videos are stored in `/app/uploads/` - implement cleanup if needed
5. **Result persistence**: Results are stored in `/app/results/` - persisted via Docker volume

---

## Mobile/Web App Integration

### iOS (Swift)

```swift
func uploadAndProcess(videoURL: URL) async throws -> Data {
    let boundary = UUID().uuidString

    // 1. Upload
    var request = URLRequest(url: URL(string: "http://localhost:5000/upload")!)
    request.httpMethod = "POST"
    request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

    let videoData = try Data(contentsOf: videoURL)
    var body = Data()
    body.append("--\(boundary)\r\n".data(using: .utf8)!)
    body.append("Content-Disposition: form-data; name=\"video\"; filename=\"video.mp4\"\r\n".data(using: .utf8)!)
    body.append("Content-Type: video/mp4\r\n\r\n".data(using: .utf8)!)
    body.append(videoData)
    body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)

    let (uploadData, _) = try await URLSession.shared.upload(for: request, from: body)
    let uploadResponse = try JSONDecoder().decode([String: String].self, from: uploadData)

    guard let filename = uploadResponse["filename"] else { throw NSError() }

    // 2. Process
    var processRequest = URLRequest(url: URL(string: "http://localhost:5000/process")!)
    processRequest.httpMethod = "POST"
    processRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
    processRequest.httpBody = try JSONEncoder().encode([
        "filename": filename,
        "static_camera": true
    ])

    let (processData, _) = try await URLSession.shared.data(for: processRequest)
    let processResponse = try JSONDecoder().decode([String: String].self, from: processData)

    guard let outputPath = processResponse["output_path"] else { throw NSError() }

    // 3. Download ZIP
    let zipURL = URL(string: "http://localhost:5000/download_zip/\(outputPath)")!
    let (zipData, _) = try await URLSession.shared.data(from: zipURL)

    return zipData
}
```

### Android (Kotlin)

```kotlin
suspend fun uploadAndProcess(videoFile: File): ByteArray {
    val client = OkHttpClient.Builder()
        .readTimeout(15, TimeUnit.MINUTES)
        .build()

    // 1. Upload
    val uploadRequest = MultipartBody.Builder()
        .setType(MultipartBody.FORM)
        .addFormDataPart("video", videoFile.name,
            videoFile.asRequestBody("video/mp4".toMediaType()))
        .build()

    val uploadResponse = client.newCall(
        Request.Builder()
            .url("http://localhost:5000/upload")
            .post(uploadRequest)
            .build()
    ).execute()

    val filename = JSONObject(uploadResponse.body!!.string())
        .getString("filename")

    // 2. Process
    val processBody = JSONObject()
        .put("filename", filename)
        .put("static_camera", true)
        .toString()
        .toRequestBody("application/json".toMediaType())

    val processResponse = client.newCall(
        Request.Builder()
            .url("http://localhost:5000/process")
            .post(processBody)
            .build()
    ).execute()

    val outputPath = JSONObject(processResponse.body!!.string())
        .getString("output_path")

    // 3. Download ZIP
    val zipResponse = client.newCall(
        Request.Builder()
            .url("http://localhost:5000/download_zip/$outputPath")
            .build()
    ).execute()

    return zipResponse.body!!.bytes()
}
```

---

## Docker Deployment

When deploying in production:

1. **Change port mapping** in [docker-compose.yml](docker-compose.yml):
   ```yaml
   ports:
     - "8080:5000"  # External:Internal
   ```

2. **Add reverse proxy** (nginx, traefik) for HTTPS

3. **Increase upload limits** in [web_app/app.py](web_app/app.py):
   ```python
   app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
   ```

4. **Add authentication** if needed

---

## Support

See main documentation:
- [CLAUDE.md](CLAUDE.md) - Architecture overview
- [MODEL_DOWNLOAD_GUIDE.md](MODEL_DOWNLOAD_GUIDE.md) - Model setup
- [BUILD_STATUS.md](BUILD_STATUS.md) - Deployment status

For issues: Check container logs with `docker compose logs -f gvhmr`
