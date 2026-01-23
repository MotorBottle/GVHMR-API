let uploadedFilename = null;

// DOM Elements
const videoFileInput = document.getElementById('videoFile');
const fileNameDisplay = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const processBtn = document.getElementById('processBtn');
const staticCameraCheckbox = document.getElementById('staticCamera');
const statusMessage = document.getElementById('statusMessage');
const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const resultsList = document.getElementById('resultsList');

// Event Listeners
videoFileInput.addEventListener('change', handleFileSelect);
uploadBtn.addEventListener('click', handleUpload);
processBtn.addEventListener('click', handleProcess);

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        fileNameDisplay.textContent = file.name;
        uploadBtn.disabled = false;
        hideMessage();
    }
}

async function handleUpload() {
    const file = videoFileInput.files[0];
    if (!file) {
        showMessage('Please select a file first', 'error');
        return;
    }

    uploadBtn.disabled = true;
    showMessage('Uploading file...', 'info');

    const formData = new FormData();
    formData.append('video', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadedFilename = data.filename;
            showMessage(`File uploaded successfully: ${data.filename}`, 'success');
            processBtn.disabled = false;
        } else {
            showMessage(`Upload failed: ${data.error}`, 'error');
            uploadBtn.disabled = false;
        }
    } catch (error) {
        showMessage(`Upload error: ${error.message}`, 'error');
        uploadBtn.disabled = false;
    }
}

async function handleProcess() {
    if (!uploadedFilename) {
        showMessage('Please upload a file first', 'error');
        return;
    }

    processBtn.disabled = true;
    uploadBtn.disabled = true;
    resultsSection.style.display = 'none';
    progressSection.style.display = 'block';
    progressBar.style.width = '10%';
    progressText.textContent = 'Starting processing...';
    showMessage('Processing video... This may take several minutes.', 'info');

    const requestData = {
        filename: uploadedFilename,
        static_camera: staticCameraCheckbox.checked
    };

    try {
        // Simulate progress (since actual progress is hard to track)
        let progress = 10;
        const progressInterval = setInterval(() => {
            if (progress < 90) {
                progress += 5;
                progressBar.style.width = progress + '%';
                progressText.textContent = `Processing... ${progress}%`;
            }
        }, 2000);

        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });

        clearInterval(progressInterval);

        const data = await response.json();

        if (response.ok) {
            progressBar.style.width = '100%';
            progressText.textContent = 'Processing complete!';
            showMessage('Video processed successfully!', 'success');

            // Show results
            setTimeout(() => {
                displayResults(data.output_path);
            }, 1000);

            // Reset form
            setTimeout(() => {
                resetForm();
            }, 2000);
        } else {
            progressBar.style.width = '0%';
            progressSection.style.display = 'none';

            let errorMsg = `Processing failed: ${data.error}`;
            if (data.missing_models) {
                errorMsg += `\nMissing models: ${data.missing_models.join(', ')}`;
            }
            if (data.stderr) {
                errorMsg += `\n\nError details:\n${data.stderr}`;
            }

            showMessage(errorMsg, 'error');
            processBtn.disabled = false;
            uploadBtn.disabled = false;
        }
    } catch (error) {
        progressBar.style.width = '0%';
        progressSection.style.display = 'none';
        showMessage(`Processing error: ${error.message}`, 'error');
        processBtn.disabled = false;
        uploadBtn.disabled = false;
    }
}

async function displayResults(outputName) {
    try {
        const response = await fetch(`/results/${outputName}`);
        const data = await response.json();

        if (response.ok && data.files.length > 0) {
            resultsSection.style.display = 'block';
            resultsList.innerHTML = '';

            // Add "Download All as ZIP" button at the top
            const zipDownloadDiv = document.createElement('div');
            zipDownloadDiv.className = 'result-file zip-download';
            zipDownloadDiv.style.borderTop = '2px solid #4CAF50';
            zipDownloadDiv.style.backgroundColor = '#f0f8f0';
            zipDownloadDiv.style.fontWeight = 'bold';

            const zipLabel = document.createElement('span');
            zipLabel.textContent = `📦 All Results (${data.files.length} files)`;

            const zipLink = document.createElement('a');
            zipLink.href = `/download_zip/${outputName}`;
            zipLink.textContent = 'Download ZIP';
            zipLink.className = 'download-zip-btn';
            zipLink.style.backgroundColor = '#4CAF50';
            zipLink.style.color = 'white';
            zipLink.style.padding = '8px 16px';
            zipLink.style.borderRadius = '4px';
            zipLink.style.textDecoration = 'none';

            zipDownloadDiv.appendChild(zipLabel);
            zipDownloadDiv.appendChild(zipLink);
            resultsList.appendChild(zipDownloadDiv);

            // Add individual files
            data.files.forEach(file => {
                const fileDiv = document.createElement('div');
                fileDiv.className = 'result-file';

                const fileName = document.createElement('span');
                fileName.textContent = file;

                const downloadLink = document.createElement('a');
                downloadLink.href = `/download/${outputName}/${file}`;
                downloadLink.textContent = 'Download';
                downloadLink.download = file;

                fileDiv.appendChild(fileName);
                fileDiv.appendChild(downloadLink);
                resultsList.appendChild(fileDiv);
            });
        } else {
            showMessage('No result files found', 'info');
        }
    } catch (error) {
        console.error('Error fetching results:', error);
    }
}

function showMessage(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
}

function hideMessage() {
    statusMessage.className = 'status-message';
    statusMessage.style.display = 'none';
}

function resetForm() {
    videoFileInput.value = '';
    fileNameDisplay.textContent = 'No file selected';
    uploadedFilename = null;
    uploadBtn.disabled = true;
    processBtn.disabled = true;
    progressSection.style.display = 'none';
}

// Health check on page load
async function checkHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        console.log('Health check:', data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

checkHealth();
