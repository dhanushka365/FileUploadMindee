const fileList = document.querySelector(".file-list");
const fileBrowseButton = document.querySelector(".file-browse-button");
const fileBrowseInput = document.querySelector(".file-browse-input");
const fileUploadBox = document.querySelector(".file-upload-box");
const fileCompletedStatus = document.querySelector(".file-completed-status");
const fileSubmitButton = document.querySelector(".file-submit-button");
const notification = document.getElementById('notification');
const notificationMessage = document.querySelector('.notification-message');
const notificationClose = document.querySelector('.notification-close');
const messageDiv = document.getElementById('message');

let totalFiles = 0;
let completedFiles = 0;
let selectedFiles = [];

const createFileItemHTML = (file, index) => {
    const { name, size } = file;
    const extension = name.split(".").pop();
    const formattedFileSize = size >= 1024 * 1024 ? `${(size / (1024 * 1024)).toFixed(2)} MB` : `${(size / 1024).toFixed(2)} KB`;

    return `<li class="file-item" id="file-item-${index}">
                <div class="file-extension">${extension}</div>
                <div class="file-content-wrapper">
                    <div class="file-content">
                        <div class="file-details">
                            <h5 class="file-name">${name}</h5>
                            <div class="file-info">
                                <small class="file-size">0 MB / ${formattedFileSize}</small>
                                <small class="file-divider">•</small>
                                <small class="file-status">Ready</small>
                            </div>
                        </div>
                        <button class="cancel-button" data-index="${index}">
                            <i class="bx bx-x"></i>
                        </button>
                    </div>
                </div>
            </li>`;
};

const removeFile = (index) => {
    // Remove the file from the selectedFiles array
    selectedFiles.splice(index, 1);

    // Remove the corresponding file item from the HTML list
    const fileItem = document.getElementById(`file-item-${index}`);
    if (fileItem) {
        fileItem.remove();
    }

    // Update totalFiles and the status
    totalFiles = selectedFiles.length;
    completedFiles = Math.min(completedFiles, totalFiles); // Ensure completedFiles doesn't exceed totalFiles

    if (totalFiles === 0) {
        fileCompletedStatus.innerText = "0 / 0 files ready for submission";
    } else {
        fileCompletedStatus.innerText = `${completedFiles} / ${totalFiles} files ready for submission`;
    }

    document.querySelectorAll(".file-item").forEach((item, newIndex) => {
        item.id = `file-item-${newIndex}`;
        item.querySelector(".cancel-button").setAttribute('data-index', newIndex);
        item.querySelector(".cancel-button").addEventListener('click', () => removeFile(newIndex));
    });
};

const handleSelectedFiles = ([...files]) => {
    if (files.length === 0) return;

    files.forEach((file) => {
        const index = selectedFiles.length; // Use the length of selectedFiles array as the index
        selectedFiles.push(file);
        const fileItemHTML = createFileItemHTML(file, index);
        fileList.insertAdjacentHTML("afterbegin", fileItemHTML);

        // Add event listener for the cancel button to remove the file
        const cancelButton = document.querySelector(`#file-item-${index} .cancel-button`);
        cancelButton.addEventListener('click', () => removeFile(index));
    });

    totalFiles = selectedFiles.length; // Update total file count
    fileCompletedStatus.innerText = `${completedFiles} / ${totalFiles} files ready for submission`;
};

const showNotification = (message, type) => {
    notificationMessage.innerText = message;
    notification.classList.add(type); // 'success' or 'error'
    notification.style.display = 'block';

    // Hide the notification after 5 seconds
    setTimeout(() => {
        notification.style.display = 'none';
        notification.classList.remove(type);
    }, 5000);
};

notificationClose.addEventListener('click', () => {
    notification.style.display = 'none';
});

const handleFileUploading = () => {
    if (selectedFiles.length === 0) {
        showNotification('Error: No files selected for upload. Please select a file.', 'error');
        return;
    }

    selectedFiles.forEach((file, index) => {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append("file", file);

        const currentFileItem = document.querySelector(`#file-item-${index}`);

        xhr.upload.addEventListener("progress", (e) => {
            const fileProgress = Math.round((e.loaded / e.total) * 100);
            currentFileItem.querySelector(".file-status").innerText = `Uploading: ${fileProgress}%`;
        });

        xhr.addEventListener("load", () => {
            completedFiles++;
            currentFileItem.querySelector(".file-status").innerText = "Completed";
            fileCompletedStatus.innerText = `${completedFiles} / ${totalFiles} files uploaded`;

            // Get the response from the Mindee API
            const response = JSON.parse(xhr.responseText);

            // Check if the upload was successful
            if (xhr.status === 201) {
                  showNotification(`Success: ${response.message}`, 'success');
                  //showNotification(`Success:\n ${JSON.stringify(response.result, null, 2)}`, 'success');
            } else {
                showNotification(`Error: ${response.message}`, 'error');
            }
        });

        xhr.addEventListener("error", () => {
            // Show error notification
            showNotification(`Failed to upload ${file.name}. Please try again.`, 'error');
        });

        xhr.open("POST", "/upload", true);
        xhr.send(formData);
    });
};

// Event listeners
fileUploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    handleSelectedFiles(e.dataTransfer.files);
    fileUploadBox.classList.remove("active");
});

fileUploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    fileUploadBox.classList.add("active");
});

fileUploadBox.addEventListener("dragleave", (e) => {
    e.preventDefault();
    fileUploadBox.classList.remove("active");
});

fileBrowseInput.addEventListener("change", (e) => handleSelectedFiles(e.target.files));
fileBrowseButton.addEventListener("click", () => fileBrowseInput.click());

// Submit button event listener
fileSubmitButton.addEventListener("click", () => handleFileUploading());
