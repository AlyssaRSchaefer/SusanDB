let unselectedFields = [];
let fields = [];
const fieldsBody = document.getElementById('layout-fields-body');
let hasChanges = false;
let sortableInstance = null;

function openFieldPopup() {
    populateFieldSelect();
    document.getElementById("field-popup").style.display = "flex";
}

function addNewField() {
    const selectedField = document.getElementById("new-field-select").value;
    if (selectedField === "") {
        alert("Please select a field.");
        return;
    }

    // Add field to the list and remove from unselectedFields
    fields.push(selectedField);
    unselectedFields = unselectedFields.filter(field => field !== selectedField);
    hasChanges = true;
    
    document.getElementById('save-fields-btn').style.display = 'inline-block';
    document.getElementById('revert-fields-btn').style.display = 'inline-block';

    // Add the new field row to the table
    const tr = document.createElement("tr");
    tr.id = "field-" + selectedField;
    tr.classList.add("templates-field-row");
    tr.innerHTML = `
        <td>
            <span class="drag-handle layout-field-name">${selectedField.toUpperCase().replace("_", " ")}</span>
            <span class="templates-delete-icon" onclick="confirmDeleteField('${selectedField}')">🗑️</span>
        </td>
    `;
    
    fieldsBody.appendChild(tr);
    
    const select = document.getElementById("new-field-select");
    select.querySelector(`option[value="${selectedField}"]`).remove();
    select.value = "";

    // Reinitialize sorting since we've modified the list
    initializeSortable();

    closeFieldPopup();
}

function closeFieldPopup() {
    document.getElementById("field-popup").style.display = "none";
}

function initializeSortable() {
    if (sortableInstance) {
        sortableInstance.destroy();
    }

    sortableInstance = new Sortable(fieldsBody, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        onEnd: function () {
            hasChanges = true;
            document.getElementById('save-fields-btn').style.display = 'inline-block'; 
            document.getElementById('revert-fields-btn').style.display = 'inline-block';
        }
    });
}

function revertLayoutChanges() {
    fetchLayout();
    hasChanges = false;
    document.getElementById('save-fields-btn').style.display = 'none';
    document.getElementById('revert-fields-btn').style.display = 'none';
}

function confirmDeleteField(fieldName) {
    if (confirm(`Are you sure you want to delete the field "${fieldName}"?`)) {
        deleteField(fieldName);
    }
}

function deleteField(fieldName) {
    let rowID = "field-" + fieldName;
    const row = document.getElementById(rowID);
    if (row) row.remove();

    // Properly remove field from the fields array
    fields = fields.filter(field => field !== fieldName);

    // Add the deleted field back to unselectedFields
    unselectedFields.push(fieldName);

    // Add the field back to the dropdown
    const select = document.getElementById("new-field-select");
    const option = document.createElement("option");
    option.value = fieldName;
    option.textContent = fieldName.toUpperCase().replace(/_/g, " ");
    select.appendChild(option); 

    hasChanges = true;
    document.getElementById('save-fields-btn').style.display = 'inline-block';
    document.getElementById('revert-fields-btn').style.display = 'inline-block';
}


function saveLayoutChanges() {
    const updatedFields = [];
    document.querySelectorAll(".layout-field-name").forEach(fieldCell => {
        updatedFields.push(fieldCell.textContent.trim().replace(" ", "_").toLowerCase());
    });

    fetch("/save_fields", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ fields: updatedFields })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("Fields updated successfully!");
            hasChanges = false;
            document.getElementById('save-fields-btn').style.display = 'none';
            document.getElementById('revert-fields-btn').style.display = 'none';
        } else {
            alert("Error updating fields.");
        }
    })
    .catch(error => console.error("Error:", error));
}

function populateFieldSelect() {
    fetch("/get_student_fields")
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById("new-field-select");
            select.innerHTML = "<option value=''> SELECT FIELD </option>"; // Reset dropdown

            unselectedFields = data.filter(field => !fields.includes(field));

            unselectedFields.forEach(field => {
                const option = document.createElement("option");
                option.value = field;
                option.textContent = field.toUpperCase().replace(/_/g, " "); // Fix toUpperCase()
                select.appendChild(option);
            });
        })
        .catch(error => console.error("Error:", error));
}

function fetchLayout() {

    fields = [];

    fetch('/get_fields')
    .then(response => response.json())
    .then(data => {
        fieldsBody.innerHTML = '';
        data.forEach(field => {
            const tr = document.createElement('tr');
            tr.id='field-'+field;
            tr.classList.add('templates-field-row');
            tr.innerHTML = "<td><span class='drag-handle layout-field-name'>"+ field.toUpperCase().replace("_", " ") +"</span><span class='templates-delete-icon' onclick='deleteField(\"" + field + "\")'>🗑️</span></td>";
            fieldsBody.appendChild(tr);           
            fields.push(field);
        })
        initializeSortable();
    })
    .catch(error => console.error('Error:', error));
}

window.onload = () => {
    fetchLayout();
};