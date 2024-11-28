const fileUploader = document.querySelector(".file-uploader");
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

const resultSection = document.getElementById('resultSection');
const pdfPreview = document.getElementById('pdfPreview');
const pdfFrame = document.getElementById('pdfFrame');
const dataFields = document.getElementById('dataFields');
const submitDataButton = document.getElementById('dataForm').querySelector('button');
const header = document.querySelector('header');
const footer = document.querySelector('footer');
const togglePreview = document.getElementById('togglePreview');

let totalFiles = 0;
let completedFiles = 0;
let selectedFiles = [];


// Show/hide file upload box
const toggleFileUploadBox = (show) => {
    fileUploader.style.display = show ? 'block' : 'none';
};

// Function to create labeled, editable text boxes based on JSON response
const populateDataFields = (jsonResponse) => {
    dataFields.innerHTML = ""; // Clear existing fields

    // Recursive function to create input fields for each key in the JSON
    const createField = (key, value, isSubField = false) => {
        const fieldWrapper = document.createElement('div');
        fieldWrapper.classList.add(isSubField ? 'sub-field-wrapper' : 'field-wrapper');

        const label = document.createElement('label');
        label.innerText = key;
        const input = document.createElement('textarea');
         input.value = value || ""; // Set to empty string if null
         input.name = key;
         input.classList.add('editable-field');

        fieldWrapper.appendChild(label);
        fieldWrapper.appendChild(input);
        return fieldWrapper;
    };

    // Recursive function to create a group container for nested objects
    const createGroupContainer = (groupName) => {
        const groupContainer = document.createElement('div');
        groupContainer.classList.add('group-container');

        const groupLabel = document.createElement('h3');
        groupLabel.innerText = groupName;
        groupContainer.appendChild(groupLabel);

        return groupContainer;
    };

    // Process each key in the JSON, including nested objects
    const processData = (data, parentKey = '', container = dataFields) => {
        for (const [key, value] of Object.entries(data)) {
            const fieldName = parentKey ? `${parentKey}.${key}` : key;

            // If it's an object, create a group container for it
            if (typeof value === 'object' && !Array.isArray(value) && value !== null) {
                const groupContainer = createGroupContainer(key);
                processData(value, fieldName, groupContainer); // Process nested objects recursively
                container.appendChild(groupContainer); // Append the group container to the specified container
            } else {
                // Append individual fields directly
                const fieldWrapper = createField(key, value, parentKey !== '');
                container.appendChild(fieldWrapper);
            }
        }
    };

    processData(jsonResponse); // Start processing from the root object
    header.style.display = 'none';  // Hide header
    footer.style.display = 'none';  // Hide footer
    // Show the result section with form and PDF preview
    resultSection.classList.remove('hidden');

    // Hide the file upload box
    toggleFileUploadBox(false);
};


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

// Function to handle file upload
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

            // Parse the response from Mindee API
            const response = JSON.parse(xhr.responseText);

            // Check if the upload was successful
            if (xhr.status === 201) {
                showNotification('File uploaded successfully', 'success');

                // Populate the form with JSON response data
                populateDataFields(response.result);

                // Display the PDF preview
                 // PDF path from response
                pdfFrame.src = response.result.file_path;
            } else {
                showNotification(`Error: ${response.message}`, 'error');
            }
        });

        xhr.addEventListener("error", () => {
            showNotification(`Failed to upload ${file.name}. Please try again.`, 'error');
        });

        xhr.open("POST", "/LightGPTFileUpload", true);
        xhr.send(formData);
    });
};

// Function to convert object to a readable string format for notification
const formatObjectForNotification = (obj) => {
    const formattedEntries = [];

    const formatData = (data, parentKey = '') => {
        for (const [key, value] of Object.entries(data)) {
            const fullKey = parentKey ? `${parentKey}.${key}` : key;
            if (typeof value === 'object' && value !== null) {
                formatData(value, fullKey);
            } else {
                formattedEntries.push(`${fullKey}: ${value}`);
            }
        }
    };

    formatData(obj);
    return formattedEntries.join('\n');
};

// Save JSON as text file
const autoSaveAsTextFile = (data, filename) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
};

// Update form data as JSON object for submission
const getUpdatedFormData = () => {
    const updatedData = {
        "type": "",
        "shippingname": "",
        "shippingstreet": "",
        "shippingcity": "",
        "shippingpostalcode": "",
        "shippingphone": "",
        "shippingemail": "",
        "instruction_notes": "",
        "fault_detail": "",
        "access_key": "",
        "propertymanagerdetails": {
            "payment_buyer_name": "",
            "paymentbuyeremail": "",
            "paymentbyerphone": ""
        },
        "file_path": "",
        "paymentcompanyname": "",
        "paymentbillingname": "",
        "paymentponumber": "",
        "email": "",
    };

    dataFields.querySelectorAll('.editable-field').forEach(input => {
        const keyPath = input.name.split('.');
        let current = updatedData;
        keyPath.forEach((key, index) => {
            if (index === keyPath.length - 1) {
                current[key] = input.value;
            } else {
                current = current[key];
            }
        });
    });

    return updatedData;
};

// Submit JSON data to webhook
const submitDataToWebhook = (jsonData) => {
    const xhr = new XMLHttpRequest();
    const webhookURL = "/webhook";  // Update with full URL if necessary

    xhr.open("POST", webhookURL, true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onload = () => {
        if (xhr.status === 200) {
            try {
                //showNotification('Data submitted successfully!', 'success');
                const response = JSON.parse(xhr.responseText);
                console.log("Server Response JSON:", response);
                // Display response in notification
                showNotification(`Data submitted to the webhook successfully! Response:\n${JSON.stringify(response, null, 2)}`, 'success');
                toggleFileUploadBox(true);
                resultSection.classList.add('hidden');

                console.log("Server Response:", xhr.responseText);  // Log server response for verification
            }catch (e) {
                console.error("Response could not be parsed as JSON:", xhr.responseText);
                showNotification('Submission succeeded, but response parsing failed.', 'warning');
            }
        } else {
            console.error(`Submission failed with status ${xhr.status}: ${xhr.statusText}`);
            console.error("Response:", xhr.responseText);
            showNotification('Failed to submit data. Please check the console for details.', 'error');
        }
    };

    xhr.onerror = () => {
        console.error("Network Error: Could not reach the webhook server.");
        showNotification('Failed to submit data due to network error.', 'error');
    };

    // Log the data being sent for verification
    console.log("Submitting JSON data:", JSON.stringify(jsonData, null, 2));

    // Send the JSON data to the webhook
    xhr.send(JSON.stringify(jsonData));
};

// Validate JSON structure before submission
const validateJsonStructure = (jsonData) => {
    const requiredFields = [
        "access_key", "email", "fault_detail", "instruction_notes", "paymentbillingname",
        "paymentcompanyname", "paymentponumber", "propertymanagerdetails.payment_buyer_name",
        "propertymanagerdetails.paymentbuyeremail", "propertymanagerdetails.paymentbyerphone",
        "shippingcity", "shippingemail", "shippingname", "shippingphone", "shippingpostalcode",
        "shippingstreet", "type", "file_path"
    ];

    for (const field of requiredFields) {
        const keys = field.split(".");
        let value = jsonData;

        for (const key of keys) {
            if (value[key] === undefined) {
                console.error(`Missing field: ${field}`);
                return false;
            }
            value = value[key];
        }
    }

    return true;
};

// Handle form data submission
const submitData = () => {
     const updatedData = getUpdatedFormData();

    // Log the data to console for verification
    console.log("Submitting JSON data:", JSON.stringify(updatedData, null, 2));

    // Validate JSON structure before sending
    if (validateJsonStructure(updatedData)) {
        autoSaveAsTextFile(updatedData, "updatedData.txt");
        submitDataToWebhook(updatedData);
    } else {
        showNotification("JSON structure is incorrect. Please check form fields.", 'error');
    }
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
// Event listeners
submitDataButton.addEventListener("click", submitData);
