const fileList = document.querySelector(".file-list");
const fileBrowseButton = document.querySelector(".file-browse-button");
const fileBrowseInput = document.querySelector(".file-browse-input");
const fileUploadBox = document.querySelector(".file-upload-box");
const fileCompletedStatus = document.querySelector(".file-completed-status");
const fileSubmitButton = document.querySelector(".file-submit-button");
const notification = document.getElementById("notification");
const notificationMessage = document.querySelector(".notification-message");
const notificationClose = document.querySelector(".notification-close");

let totalFiles = 0;
let completedFiles = 0;
let selectedFiles = [];
let dropdownOptionsCache = ""; // Cache dropdown options for reuse

// Utility function to format file sizes
const formatFileSize = (size) => {
  return size >= 1024 * 1024
    ? `${(size / (1024 * 1024)).toFixed(2)} MB`
    : `${(size / 1024).toFixed(2)} KB`;
};

// Fetch dropdown options once and cache them
const fetchDropdownOptions = async () => {
  if (dropdownOptionsCache) return dropdownOptionsCache; // Return cached options

  try {
    const response = await fetch("https://v3.dandsappliances.com/index.php?r=api/clients-list"); // Replace with your API endpoint
    if (!response.ok) throw new Error("Failed to fetch dropdown options");
    const options = await response.json(); // Assuming the response is a JSON array
    dropdownOptionsCache = `
      <option value="" disabled selected>Select client here</option>
      ${options
        .map((option) => `<option value="${option.id}">${option.clientname}</option>`)
        .join("")}
    `;
    return dropdownOptionsCache;
  } catch (error) {
    console.error("Error fetching dropdown options:", error);
    return `<option value="error">Error fetching options</option>`;
  }
};

// Create HTML for a file item
const createFileItemHTML = async (file, index) => {
  const { name, size } = file;
  const extension = name.split(".").pop();
  const formattedFileSize = formatFileSize(size);

  // Fetch dropdown options
  const dropdownOptions = await fetchDropdownOptions();

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
                <div class="file-dropdown-wrapper">
                    <select class="file-dropdown" data-index="${index}">
                        ${dropdownOptions}
                    </select>
                </div>
            </div>
        </li>`;
};

// Remove a file and update UI
const removeFile = (index) => {
  selectedFiles.splice(index, 1); // Remove file from array
  document.getElementById(`file-item-${index}`)?.remove(); // Remove from DOM

  // Update indices and reassign IDs
  document.querySelectorAll(".file-item").forEach((item, newIndex) => {
    item.id = `file-item-${newIndex}`;
    const cancelButton = item.querySelector(".cancel-button");
    cancelButton.dataset.index = newIndex;
    cancelButton.onclick = () => removeFile(newIndex);
  });

  totalFiles = selectedFiles.length;
  completedFiles = Math.min(completedFiles, totalFiles);
  updateFileStatus();
};

// Update file status display
const updateFileStatus = () => {
  fileCompletedStatus.innerText =
    totalFiles === 0
      ? "0 / 0 files ready for submission"
      : `${completedFiles} / ${totalFiles} files ready for submission`;
};

// Handle selected files
const handleSelectedFiles = async (files) => {
  for (const file of files) {
    const index = selectedFiles.length;
    selectedFiles.push(file);

    const fileItemHTML = await createFileItemHTML(file, index);
    fileList.insertAdjacentHTML("beforeend", fileItemHTML);

    // Attach event listener to cancel button
    const cancelButton = document.querySelector(`#file-item-${index} .cancel-button`);
    cancelButton.onclick = () => removeFile(index);
  }

  totalFiles = selectedFiles.length;
  updateFileStatus();
};

// Show notification
const showNotification = (message, type) => {
  notificationMessage.innerText = message;
  notification.className = `notification ${type}`; // Add 'success' or 'error'
  notification.style.display = "block";

  setTimeout(() => (notification.style.display = "none"), 5000);
};

// Upload files
const handleFileUploading = () => {
  if (selectedFiles.length === 0) {
    showNotification("Error: No files selected for upload. Please select a file.", "error");
    return;
  }

  selectedFiles.forEach((file, index) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);

    const dropdown = document.querySelector(`#file-item-${index} .file-dropdown`);
      // Fetch both client ID and client name
    const selectedClientId = dropdown ? dropdown.value : "";
    const selectedClientName = dropdown ? dropdown.options[dropdown.selectedIndex].text : "";
    //showNotification(`Selected Client: ${selectedClientName}`, "success");
    if (!selectedClientId) {
      showNotification(`Error: No client selected for file ${file.name}.`, "error");
      return;
    }

     // Append client ID and client name to FormData
    formData.append("client_id", selectedClientId);
    formData.append("client_name", selectedClientName);

    const currentFileItem = document.querySelector(`#file-item-${index}`);

    xhr.upload.addEventListener("progress", (e) => {
      const progress = Math.round((e.loaded / e.total) * 100);
      currentFileItem.querySelector(".file-status").innerText = `Uploading: ${progress}%`;
    });

    xhr.onload = () => {
      completedFiles++;
      currentFileItem.querySelector(".file-status").innerText = "Completed";
      updateFileStatus();

      const response = JSON.parse(xhr.responseText);
      if (xhr.status === 201) {
        showNotification(`Success:\n${JSON.stringify(response.result, null, 2)}`, "success");
      } else {
        showNotification(`Error: ${response.message}`, "error");
      }
    };

    xhr.onerror = () => {
      showNotification(`Failed to upload ${file.name}. Please try again.`, "error");
    };

    xhr.open("POST", "/GPTUpload", true);
    xhr.send(formData);
  });
};

// Event listeners
fileUploadBox.addEventListener("drop", (e) => {
  e.preventDefault();
  handleSelectedFiles(e.dataTransfer.files);
  fileUploadBox.classList.remove("active");
});

fileUploadBox.addEventListener("dragover", (e) => e.preventDefault());
fileUploadBox.addEventListener("dragleave", (e) => fileUploadBox.classList.remove("active"));
fileBrowseInput.addEventListener("change", (e) => handleSelectedFiles(e.target.files));
fileBrowseButton.addEventListener("click", () => fileBrowseInput.click());
fileSubmitButton.addEventListener("click", () => handleFileUploading());
notificationClose.addEventListener("click", () => (notification.style.display = "none"));

document.addEventListener("DOMContentLoaded", () => {
  const port = window.location.port;
  const environment = port === "8001" ? "PROD" : "DEV";

  fetch("/health_check")
    .then((response) => (response.ok ? response.text() : Promise.reject("Failed to fetch container ID")))
    .then((containerId) => {
      document.querySelector(".uploader-title").textContent = `Upload Your Work Orders - ${environment} INSTANCE (${containerId})`;
    })
    .catch((error) => console.error("Error fetching container ID:", error));
});
