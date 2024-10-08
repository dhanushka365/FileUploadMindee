document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const messageDiv = document.getElementById('message');
    const uploadButton = document.getElementById('uploadButton');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    // Show loading animation
    uploadButton.classList.add('loading');
    uploadButton.innerText = 'Uploading...';

    try {
        const response = await fetch('http://localhost:8001/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        if (response.ok) {
            messageDiv.innerText = 'File uploaded successfully:\n' + JSON.stringify(data.result, null, 2);
            fileInput.value = '';
        } else {
            messageDiv.innerText = 'Error: ' + (data.message || 'Upload failed.');
        }
    } catch (error) {
        messageDiv.innerText = 'Network error. Please try again.';
    } finally {
        // Remove loading state
        uploadButton.classList.remove('loading');
        uploadButton.innerText = 'Upload';
    }
});
