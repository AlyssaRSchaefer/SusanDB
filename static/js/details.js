const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');
const table = document.getElementById("details-table");
const heading = document.querySelector("h1");
const filesContainer = document.getElementById("details-file-icons");
const noFilesIndicator = document.getElementById("details-no-files-indicator");
const loadingSpinner = document.getElementById("details-loading-spinner");
const fileOptions = document.getElementById("details-file-options");
let selectedFile = "";

function openDetailsUploadPage(){
    const studentId = encodeURIComponent(id);
    window.location.href = `/details_upload?id=${studentId}`;
}

function updateCellData(id, field, newValue) {
    fetch('/update_database_cell', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id: id, field: field, newValue: newValue })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Error: " + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('There was an issue updating the data.');
    });
}

function encodeFileId(fileName) {
    return "file-" + btoa(fileName); // base64-encode the filename
}

function addFileDiv(fileName){
    const encodedId = encodeFileId(fileName);
    const div = document.createElement("div");
    div.classList = "details-file";
    div.innerHTML = `
        <div class="details-file-icon" id="${encodedId}" onclick="selectFile('${fileName}')">
            <img src="static/icons/icon-file.png" alt="File">
        </div>
        <div class="details-file-name">${fileName}</div>
    `;    
    filesContainer.appendChild(div);

    setTimeout(() => {
        div.classList.add("appear");
    }, 10);
}

function selectFile(fileName) {
    if (selectedFile === fileName) {
        deselectFile(fileName);
        selectedFile = "";
        closeFileOptionsMenu();
        return;
    }
    if (selectedFile !== "") {
        deselectFile(selectedFile);
    }
    selectedFile = fileName;
    openFileOptionsMenu();
    const file = document.getElementById(encodeFileId(fileName));
    if (file) file.style.backgroundColor = "var(--secondary-color)";
}

function deselectFile(fileName) {
    const file = document.getElementById(encodeFileId(fileName));
    if (file) file.style.backgroundColor = "var(--tertiary-color)";
}

function openFileOptionsMenu(){
    fileOptions.style.display = "flex";
}

function closeFileOptionsMenu(){
    fileOptions.style.display = "none";
}

function openConfirmDeletePopup() {
    let popup = document.getElementById("database-confirm-delete-menu");
    popup.style.display = "flex";
}

function hideConfirmDeletePopup() {
    let popup = document.getElementById("database-confirm-delete-menu");
    popup.style.display = "none";
}

function deleteFile() {
    loading.style.display = "flex";
    fetch('/delete_student_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ student_id: id, file_name: selectedFile })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            document.getElementById("details-file-icons").innerHTML = "";
            fetchStudentFiles(id);
            selectedFile = "";
            closeFileOptionsMenu();
            hideConfirmDeletePopup();
            loading.style.display = "none";
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('There was an issue deleting the file.');
    });
}

function downloadSelectedFile() {
    fetch('/download_student_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ student_id: id, file_name: selectedFile })
    })
    .then(response => response.blob())  // Make sure to return the blob here
    .then(blob => {
        if (!blob) {
            alert("Error: No file received.");
            return;
        }
        
        // Trigger file download by creating a link and clicking it programmatically
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = selectedFile;
        link.click();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('There was an issue downloading the file.');
    });
}

function fetchStudentById(studentId) {
    fetch('/get_student', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: studentId })
    })
    .then(response => response.json())
    .then(data => {

        if (data.first_name && data.last_name) {
            heading.textContent = data.first_name + " " + data.last_name;
        } else {
            heading.textContent = "Student Details"; // Fallback text if 'name' is missing
        }

        table.innerHTML = ""; // Clear previous content

        Object.keys(data).forEach(key => {
            const tr = document.createElement("tr");
            const td_field = document.createElement("td");
            const td_value = document.createElement("td");
    
            td_field.innerHTML = key.toUpperCase().replaceAll("_", " ");
            td_value.innerHTML = data[key]; // Access the value by key
            
            td_value.ondblclick = function () {
                const originalText = td_value.innerHTML;
                const input = document.createElement('input');
                input.type = 'text';
                input.value = originalText;
                input.classList.add("details-cell-input");
                input.style.width = `${Math.max(originalText.length * 8, 50)}px`; 
                td_value.innerHTML = '';
                td_value.appendChild(input);
                input.focus();
            
                function resizeInput() {
                    const span = document.createElement("span");
                    span.style.visibility = "hidden";
                    span.style.whiteSpace = "pre";
                    span.style.font = getComputedStyle(input).font;
                    span.textContent = input.value || " "; // Avoid width collapse
                    document.body.appendChild(span);
            
                    input.style.width = `${span.offsetWidth + 5}px`; // Add small padding
                    document.body.removeChild(span);
                }
            
                input.addEventListener("input", resizeInput);
                resizeInput(); // Initial resize based on current text

                // Save the edited value when user presses Enter
                input.onblur = function () {
                    td_value.innerHTML = input.value;
                    // Optionally, send the updated data to the server
                    updateCellData(studentId, key, input.value);
                };

                input.onkeydown = function (e) {
                    if (e.key === 'Enter') {
                        td_value.innerHTML = input.value;
                        // Optionally, send the updated data to the server
                        updateCellData(studentId, key, input.value);
                    }
                };
            };    

            tr.appendChild(td_field);
            tr.appendChild(td_value);
            table.appendChild(tr);
        });
    })
    .catch(error => console.error('Error:', error));    
}

function fetchStudentFiles(studentId) {
    loadingSpinner.style.display = "flex";
    fetch('/get_student_files', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ student_id: studentId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error("Error fetching files:", data.error);
            return;
        }

        filesContainer.innerHTML = ""; // Clear previous files before adding new ones
        
        if (data.files.length === 0){
            noFilesIndicator.style.display = "block";
            loadingSpinner.style.display = "none";
            return;
        }

        data.files.forEach(fileName => {
            addFileDiv(fileName);
        });
        loadingSpinner.style.display = "none";
    })
    .catch(error => {
        console.error("Error:", error);
    });
}

window.onload = () => {
    fetchStudentById(id);
    fetchStudentFiles(id);
};