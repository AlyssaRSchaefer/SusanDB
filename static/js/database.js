let sort = {}
let columns = [];
let selectedStudents = []; 
let studentIDs = [];
let filter = [];
let search = "";
let allStudentsSelected = false;

/* SEARCH LOGIC */
const searchTerm = document.getElementById("database-search-term");
searchTerm.addEventListener("keydown", function(event){
    if (event.key === "Enter"){
        search = searchTerm.value;
        fetchData(sort, filter, search);
    }
});

/* FILTER LOGIC */
function createFilter(){
    const fieldSelect = document.getElementById("database-filter-field");
    const valueSelect = document.getElementById("database-filter-value");
    let field = fieldSelect.value;
    let value = valueSelect.value;
    createPill(field, value);
    toggleFilterPopup();
}

function toggleFilterPopup() {
    const popup = document.getElementById("database-filter-popup");
    const database = document.getElementById("database");
    
    if (popup.style.display === "none" || popup.style.display === "") {
        popup.style.display = "flex"; //
        database.style.display = "none";
    } else {
        document.getElementById("database-filter-field").selectedIndex = 0;
        document.getElementById("database-filter-value").innerHTML = '';
        popup.style.display = "none";
        database.style.display = "block";
    }
}

function createPill(field, value){
    let pillID = field + "-" + value;
    console.log(pillID);
    if (filter.includes(pillID)) return;
    const pill = document.createElement("div");
    pill.classList.add("pill");
    pill.id = pillID;
    pill.innerHTML = `
        <div class="pill-content">${field.toUpperCase()}: ${value.toUpperCase()}</div>
        <img class="pill-icon" src="/static/icons/icon-close.png" onclick="deletePill('${pillID}')">
    `;    
    
    let pillBox = document.getElementById("database-pill-box");
    pillBox.appendChild(pill);

    if (filter.length === 0) openPillMenu();
    filter.push(pillID);
    fetchData(sort, filter, search);
    console.log(filter);
}

function deletePill(pillID){
    document.getElementById(pillID).remove();
    filter = filter.filter(item => item !== pillID);
    if (filter.length === 0) closePillMenu();
    fetchData(sort, filter, search);
}

function openPillMenu(){
    const pillMenu = document.getElementById("database-pill-box");
    pillMenu.style.display = "flex";
    
    const databaseControls = document.getElementById("database-controls");
    databaseControls.style.marginBottom = "12px"
}

function closePillMenu(){
    const pillMenu = document.getElementById("database-pill-box");
    pillMenu.style.display = "none";
    
    const databaseControls = document.getElementById("database-controls");
    databaseControls.style.marginBottom = "25px"
}

/* LOGIC TO HANDLE CHECKBOXES */
function selectStudent(id){
    if (allStudentsSelected) {
        allStudentsSelected = false;
        document.getElementById("select-all-checkbox").checked = false;
    }
    let rowID = "database-row-" + id;
    let row = document.getElementById(rowID);
    if (!selectedStudents.includes(id)) {
        selectedStudents.push(id);
        row.classList.add("database-selected-row"); 
    } else {
        selectedStudents = selectedStudents.filter(studentID => studentID !== id);
        row.classList.remove("database-selected-row");
    }
}

function selectAll() {
    allStudentsSelected = !allStudentsSelected;
    selectedStudents = allStudentsSelected ? [...studentIDs] : [];
    
    const checkboxes = document.querySelectorAll('.database-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = allStudentsSelected; // Check/uncheck all
    });
    
    const rows = document.querySelectorAll('.database-table tbody tr');
    rows.forEach(row => {
        row.classList.toggle("database-selected-row", allStudentsSelected);
    });
}

/* SORT LOGIC */

function updateSortUI(field){
    let iconID = "database-icon-" + field;
    let icon = document.getElementById(iconID);
    let columnHeader = document.getElementById(field);
    
    if (icon) {
        if (sort[field] === "ASC") {
            icon.src = "static/icons/icon-up.png";
            icon.style.display = "inline";
        } else if (sort[field] === "DESC") {
            icon.src = "static/icons/icon-down.png";
            icon.style.display = "inline";
        } else {
            icon.style.display = "none";
        }
    }

    if (columnHeader) {
        columnHeader.style.backgroundColor = sort[field] ? "var(--secondary-color-highlight)" : "";
    }
}

function sortTableByField(field){
    
    // Determine the new sort state
    if (!(field in sort)) {
        sort[field] = "ASC"; // Not in sort → Add as ASC
    } else if (sort[field] === "ASC") {
        sort[field] = "DESC"; // ASC → Change to DESC
    } else {
        delete sort[field]; // DESC → Remove from sort
    }

    updateSortUI(field);
    fetchData(sort, filter, search);
}

/* Details page uses this to store selected student id in session*/
function storeSelectedStudents(){
    return fetch('/store-selected-students', {  // Added "return" here
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ selectedStudents: selectedStudents })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json(); // Ensure response is processed
    })
    .catch(error => console.error('Error:', error));
}

function openGenerateReportPage() {
    if (selectedStudents.length === 0) {
        alert("Please select at least one student to generate a report.");
        return;
    }

    // Convert selected student IDs into a query string
    const queryString = selectedStudents.map(id => `ids[]=${encodeURIComponent(id)}`).join('&');

    // Redirect to the report page with the selected student IDs as query parameters
    window.location.href = `/generate_report?${queryString}`;
}

function openDetailsPage(){
    if (!(selectedStudents.length === 1)){
        alert("Please select exactly one student to view their details");
        return;
    }
    
    storeSelectedStudents()
    .then(() => {
        window.location.href = '/details'; 
    })
    .catch(error => console.error('Error:', error));
}

function deleteStudents() {
    fetch('/delete_students_from_db', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ ids: selectedStudents })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            fetchData();
            alert("Students deleted successfully!");
        } else if (data.error) {
            console.error("Error:", data.error);
            alert("Error: " + data.error);
        }
    })
    .catch(error => console.error("Fetch error:", error));
}

/* LOGIC TO UPDATE A DATABSE VALUE WHEN THE USER EDITS A TABLE CELL */
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

/* LOGIC TO LOAD IN TABLE COLUMNS FROM FIELD ORDER FILE */
function fetchColumns() {
    const tableHeader = document.getElementById("database-head");

    fetch('/get_fields')
    .then(response => response.json())
    .then(data => {
        tableHeader.innerHTML = '';
        
        // Create checkbox for select all
        const thCheckbox = document.createElement("th");
        thCheckbox.innerHTML = `<input type="checkbox" id="select-all-checkbox" onclick="selectAll()">`;
        tableHeader.appendChild(thCheckbox);

        data.forEach(field => {
            const th = document.createElement("th");
            th.id = field;
            th.classList.add("database-column-name");
            th.onclick = () => sortTableByField(field);
            th.innerHTML = field.replace("_", " ").toUpperCase() + '<img id="database-icon-' + field + '" class="database-sort-icon" src="static/icons/icon-up.png" alt="Sort icon"></img>';
            tableHeader.appendChild(th);
            columns.push(field);
        })
        fetchData();
    })
    .catch(error => console.error('Error:', error));
}

/* LOGIC TO FETCH TABLE DATA */
function fetchData(sort = { name: 'ASC' }, filter = [], search="") {
    const table = document.getElementById('database-body');
    studentIDs = [];

    fetch('/get_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ sort: sort, filter: filter, search: search })
    })
    .then(response => response.json())
    .then(data => {
        table.innerHTML = '';
        data.forEach(row => {
            const tr = document.createElement("tr");
            tr.id = "database-row-" + row["id"];

            const trCheckbox = document.createElement("td");
            trCheckbox.innerHTML = `<input type="checkbox" class="database-checkbox" id="database-checkbox-`+ row["id"] + `" onclick="selectStudent(`+ row["id"] +`)">`;
            tr.appendChild(trCheckbox);

            // Loop through columns to ensure correct order
            columns.forEach(col => {
                const td = document.createElement("td");
                let cellText = row[col] !== undefined ? String(row[col]) : '';

                // Highlight search term
                if (search.trim() !== '' && typeof cellText === 'string') {
                    const regex = new RegExp(`(${search})`, 'gi');
                    cellText = cellText.replace(regex, '<span class="database-highlight">$1</span>');
                }

                td.innerHTML = cellText;

                td.ondblclick = function () {
                    const originalText = td.innerHTML;
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.value = originalText.replace(/<span.*?>.*?<\/span>/g, ''); // Remove highlighted text
                    input.classList.add("database-cell-input");
                    input.style.width = `${Math.max(originalText.length * 8, 50)}px`; // Ensure a minimum width
                    td.innerHTML = '';
                    td.appendChild(input);
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
                        td.innerHTML = input.value;
                        // Optionally, send the updated data to the server
                        updateCellData(row["id"], col, input.value);
                    };

                    input.onkeydown = function (e) {
                        if (e.key === 'Enter') {
                            td.innerHTML = input.value;
                            // Optionally, send the updated data to the server
                            updateCellData(row["id"], col, input.value);
                        }
                    };
                };

                tr.appendChild(td);
            });

            table.appendChild(tr);
            studentIDs.push(row["id"]);
        });
    })
    .catch(error => console.error('Error:', error));
}

async function populateFieldSelect() {
    try {
        const response = await fetch('/get_student_fields');
        const fields = await response.json();
        const select = document.getElementById("database-filter-field");
        select.innerHTML = '<option value="">SELECT FIELD</option>';

        fields.forEach(field => {
            const option = document.createElement('option');
            option.value = field;
            option.textContent = field.toUpperCase().replace("_", " ");
            select.appendChild(option);
        });
    } catch (error) {
        console.error("Error fetching student fields:", error);
    }
}

function populateValueSelect(selectedField) {
    const select = document.getElementById("database-filter-value");

    fetch('/get_field_values', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ field: selectedField })
    })
    .then(response => response.json())
    .then(data => {
        // Clear previous options
        select.innerHTML = '<option value="">SELECT VALUE</option>';

        // Populate select options
        data.forEach(value => {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value;
            select.appendChild(option);
        });
    })
    .catch(error => console.error('Error fetching field values:', error));
}

document.getElementById("database-filter-field").addEventListener("change", function() {
    const selectedField = this.value;
    populateValueSelect(selectedField);
});

window.onload = () => {
    fetchColumns();
    populateFieldSelect();
};
