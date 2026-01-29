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
  "static_camera": true
}
```

**Parameters:**
- `filename` (string, required): Name returned from upload endpoint
- `static_camera` (boolean, optional):
  - `true`: Use static camera mode (faster, no DPVO required)
  - `false`: Use moving camera mode (requires DPVO model)
  - Default: `true`

**Example:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"filename":"video.mp4","static_camera":true}' \
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

# 2. Process video
print("Processing video... (this may take 5-10 minutes)")
response = requests.post(
    f"{API_URL}/process",
    json={
        "filename": filename,
        "static_camera": True
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

    // 2. Process video
    console.log('Processing video... (this may take 5-10 minutes)');
    const processResponse = await axios.post(`${API_URL}/process`, {
        filename: filename,
        static_camera: true
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

The ZIP contains these files:

- `hmr4d_results.pt` - Main SMPL parameters (body pose, shape, translation)
- `preprocess/vitpose.pt` - 2D keypoint detections
- `preprocess/vit_features.pt` - Deep learning features
- `preprocess/bbx.pt` - Bounding boxes
- `preprocess/slam_results.pt` - Camera poses
- `render.mp4` - Visualization video (if generated)

See [CLAUDE.md](CLAUDE.md) for detailed file format documentation.

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

- **Processing time**: 5-10 minutes per video (depends on length and GPU)
- **Concurrent requests**: Process one video at a time (no queue system currently)
- **Timeout**: Set client timeout to 15+ minutes for long videos
- **GPU memory**: ~8GB VRAM recommended

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
