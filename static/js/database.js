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
        <div class="pill-content">${field.toUpperCase()}: ${value.toUpperCase()} ${pillID}</div>
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
    selectedStudents.includes(id) ? selectedStudents.pop(id) : selectedStudents.push(id)
    let rowID = "database-row-" + id;
    let row = document.getElementById(rowID);
    selectedStudents.includes(id) ? row.style.backgroundColor = "var(--secondary-color-highlight)" : row.style.backgroundColor = "var(--tertiary-color)";
}

function selectAll(){
    newBackgroundColor = ""
    newCheckedStatus = true;

    if (allStudentsSelected === false){
        selectedStudents = studentIDs;
        newBackgroundColor = "var(--secondary-color-highlight)";
        allStudentsSelected = true;
    }
    else {
        selectedStudents = [];
        newBackgroundColor = "var(--tertiary-color)";
        newCheckedStatus = false;
        allStudentsSelected = false;
    }
    
    const checkboxes = document.querySelectorAll('.database-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = newCheckedStatus; // Set each checkbox as checked
    });

    const rows = document.querySelectorAll('.database-table tr');
    rows.forEach((row) => {
        row.style.backgroundColor = newBackgroundColor;
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

/* LOGIC TO SEND DATA TO OTHER PAGES */
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

function openGenerateReportPage(){
    if (selectedStudents.length === 0){
        return;
    }
    
    storeSelectedStudents()
    .then(() => {
        window.location.href = '/generate-report'; 
    })
    .catch(error => console.error('Error:', error));
}

function openDetailsPage(){
    if (!(selectedStudents.length === 1)){
        return;
    }
    
    storeSelectedStudents()
    .then(() => {
        window.location.href = '/details'; 
    })
    .catch(error => console.error('Error:', error));
}

/* LOGIC TO LOAD IN TABLE COLUMNS FROM FIELD ORDER FILE */
function fetchColumns() {
    const tableHeader = document.querySelector('table thead');

    fetch('/get_fields')
    .then(response => response.json())
    .then(data => {
        tableHeader.innerHTML = '';
        
        // Create checkbox for select all
        const thCheckbox = document.createElement("th");
        thCheckbox.innerHTML = `<input type="checkbox" id="select-all-checkbox" onclick="selectAll()">`;
        tableHeader.appendChild(thCheckbox);

        data.forEach(field => {
            const td = document.createElement("td");
            td.id = field;
            td.classList.add("database-column-name");
            td.onclick = () => sortTableByField(field);
            td.innerHTML = field.replace("_", " ").toUpperCase() + '<img id="database-icon-' + field + '" class="database-sort-icon" src="static/icons/icon-up.png" alt="Sort icon"></img>';
            tableHeader.appendChild(td);
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
        body: JSON.stringify({ field: selectedField }) // Corrected JSON key
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
