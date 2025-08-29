const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');
const table = document.getElementById("details-table");
const heading = document.querySelector("h1");
const filesContainer = document.getElementById("details-file-icons");
const noFilesIndicator = document.getElementById("details-no-files-indicator");
const loadingSpinner = document.getElementById("details-loading-spinner");
const fileOptions = document.getElementById("details-file-options");
let selectedFile = "";


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

            tr.appendChild(td_field);
            tr.appendChild(td_value);
            table.appendChild(tr);
        });
    })
    .catch(error => console.error('Error:', error));    
}

window.onload = () => {
    fetchStudentById(id);
};