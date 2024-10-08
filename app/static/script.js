document.getElementById('uploadForm').addEventListener('submit', async (event) => {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const messageDiv = document.getElementById('message');
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('http://localhost:8001/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();
        if (response.ok) {
            messageDiv.innerText = 'File uploaded successfully:\n' + JSON.stringify(data.result, null, 2);
        } else {
            messageDiv.innerText = 'Error: ' + (data.message || 'Upload failed.');
        }
    } catch (error) {
        messageDiv.innerText = 'Network error. Please try again.';
    }
});
