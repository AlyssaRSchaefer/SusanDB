const dataElement = document.getElementById('template-data');
let session_mode = null;
let templatesDict = null;
let originalTemplatesDict = null;
let all_fields = null;
if(dataElement) {
    session_mode = dataElement.getAttribute('data-session-mode');
    // Check the session mode. if they are in view, do not allow buttons to be clicked that would lead to onedrive changes
    templatesDict = JSON.parse(dataElement.getAttribute('data-templates'));
    originalTemplatesDict = JSON.parse(dataElement.getAttribute('data-templates')); // kept for reverts
    all_fields = JSON.parse(dataElement.getAttribute('data-fields'));
} else {
    // Fallback values for testing purposes
    session_mode = "edit";
    templatesDict = { test: ['A', 'B'] };
    originalTemplatesDict = { test: ['A', 'B'] };
    all_fields = ['A', 'B', 'C', 'D'];
}    

let currentTemplate = null;
let hasChanges = false;
let sortableInstance = null;

// Function to show the alert if there are unsaved changes
function confirmUnsavedChanges(event) {
    //extra check to make sure not in view mode
    if (hasChanges && session_mode!="view") {
        const message = "You have unsaved changes. Are you sure you want to leave?";
        event.returnValue = message; // For modern browsers
        return message; // For older browsers (deprecated but still works in some cases)
    }
}

function revertTemplateChanges() {
    //extra check to make sure not in view mode
    if(session_mode=="view"){
      return
    }
    const userConfirmed = confirm("Are you sure you want to revert changes made?");
    if (!userConfirmed) {
        return;
    } else {
        templatesDict[currentTemplate] = [...originalTemplatesDict[currentTemplate]]; // Restore from original
        hasChanges = false;
        loadTemplateFields(currentTemplate, true);
        document.getElementById('save-fields-btn').style.display = 'none';
        document.getElementById('revert-fields-btn').style.display = 'none';
    }
}

function loadTemplateFields(templateName, from_field = false) {
    if (hasChanges && !from_field && session_mode!="view") {
        const userConfirmed = confirm("You have unsaved changes. Are you sure you want to switch templates?");
        if (!userConfirmed) {
            return; // Stop the template loading if the user cancels
        } else {
            hasChanges = false;
            templatesDict[currentTemplate] = [...originalTemplatesDict[currentTemplate]]; // Restore from original
            document.getElementById('save-fields-btn').style.display = 'none';
            document.getElementById('revert-fields-btn').style.display = 'none';
        }
    }

    currentTemplate = templateName;
    const fields = [...templatesDict[templateName]]; // Make a copy of the fields
    document.getElementById('template-name-header').textContent = `${templateName} FIELDS`;

    const fieldsBody = document.getElementById('template-fields-body');
    fieldsBody.innerHTML = ''; // Clear existing fields

    // Loop through fields to create rows with a delete icon in a separate cell
    fields.forEach(field => {
        const row = document.createElement('tr');
        const cell = document.createElement('td');

        // Create a cell for the field name
        const fieldCell = document.createElement('span');
        fieldCell.classList.add('drag-handle');
        fieldCell.classList.add('templates-field-name');
        fieldCell.style.textAlign = 'center'; // Center the field name
        fieldCell.textContent = field;

        cell.appendChild(fieldCell);

        //ONLY ALLOW DELETE IF IN EDIT MODE
        if(session_mode!='view'){
          const deleteIcon = document.createElement('span');
          deleteIcon.classList.add('templates-delete-icon'); // Reuse existing class
          deleteIcon.textContent = '🗑️';
          deleteIcon.onclick = () => confirmDeleteField(field);
          cell.appendChild(deleteIcon);
        }
        
        row.appendChild(cell);
        row.classList.add('templates-field-row');

        fieldsBody.appendChild(row);
    });

    // Reinitialize Sortable after loading new fields
    if (sortableInstance) {
        sortableInstance.destroy(); // Destroy the old instance to prevent duplication
    }

    if(session_mode!="view"){
      sortableInstance = new Sortable(fieldsBody, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        onEnd: function () {
            hasChanges = true; // Mark as changed
            document.getElementById('save-fields-btn').style.display = 'inline-block'; // Show save button
            document.getElementById('revert-fields-btn').style.display = 'inline-block';
        }
      });
    }

    // Initially hide the save button when there are no changes
    document.getElementById('fields-section').style.display = "flex";
}

function confirmDeleteField(fieldName) {
    //extra check to make sure not in view mode
    if(session_mode=="view"){
      return
    }
    if (confirm(`Are you sure you want to delete the field "${fieldName}"?`)) {
        deleteField(fieldName);
    }
}

function deleteField(fieldName) {
    const index = templatesDict[currentTemplate].indexOf(fieldName);
    if (index > -1) {
        templatesDict[currentTemplate].splice(index, 1);
        loadTemplateFields(currentTemplate, true);
        hasChanges = true;
        document.getElementById('save-fields-btn').style.display = 'inline-block';
        document.getElementById('revert-fields-btn').style.display = 'inline-block';
    }
}

function saveTemplateChanges() {
    //extra check to make sure not in view mode
    if(session_mode=="view"){
      return
    }
    const fields = [];
    document.querySelectorAll(".templates-field-name").forEach(fieldCell => {
        const fieldName = fieldCell.textContent.trim();
        if (fieldName) fields.push(fieldName);
    });

    templatesDict[currentTemplate] = fields; 
    loading.style.display = "flex";

    fetch("/api/update_template", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: currentTemplate,
            columns: fields
        })
    }).then(response => response.json()).then(data => {
        loading.style.display = "none";
        if (data.message) {
            alert("Template updated successfully!");
            hasChanges = false; // Reset change flag after save
            document.getElementById('save-fields-btn').style.display = 'none'; // Hide save button
            document.getElementById('revert-fields-btn').style.display = 'none';

            // Update originalTemplatesDict
            originalTemplatesDict[currentTemplate] = [...templatesDict[currentTemplate]]; 

        } else {
            alert("Error updating template.");
        }
    }).catch(error => {
        console.error("Error:", error);
    });
}

function delete_template(templateName) {
    //extra check to make sure not in view mode
    if(session_mode=="view"){
      return
    }
    const userConfirmed = confirm(`Are you sure you want to delete the template "${templateName}"?`);
    if (userConfirmed) {
        // Send a POST request to delete the template
        loading.style.display = "flex";
        fetch("/api/delete_template", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ name: templateName })
        })
        .then(response => response.json())
        .then(data => {
            loading.style.display = "none";
            if (data.message) {
                // Delete the row by ID
                const rowToDelete = document.getElementById(`template-${templateName}`);
                if (rowToDelete) {
                    rowToDelete.remove();
                } else {
                    alert("Error: Row not found.");
                }
            } else {
                alert("Error: " + data.error); // Handle errors (template not found, etc.)
            }
        })
        .catch(error => {
            loading.style.display = "none";
            console.error("Error:", error);
            alert("An error occurred while deleting the template.");
        });
    }
}

function openFieldPopup() {
    if (!currentTemplate) {
        alert("Please select a template first.");
        return;
    }

    // Calculate available fields, ignoring case
    const normalizedCurrentFields = templatesDict[currentTemplate].map(field =>
        field.toLowerCase()
    );
    const availableFields = all_fields.filter(field =>
        !normalizedCurrentFields.includes(field.toLowerCase())
    );

    // Populate the dropdown with the calculated available fields
    const selectElement = document.getElementById("new-field-select");
    selectElement.innerHTML = ""; // Clear existing options
    selectElement.innerHTML += '<option value="">-- Select Field --</option>';
    availableFields.forEach(field => {
        const option = document.createElement("option");
        option.value = field;
        option.text = field.toUpperCase();
        selectElement.appendChild(option);
    });

    document.getElementById("field-popup").style.display = "flex";
}

function addNewField() {
    const selectedField = document.getElementById("new-field-select").value;
    if (selectedField === "") {
        alert("Please select a field.");
        return;
    }

    const normalizedSelectedField = selectedField.toUpperCase();

    if (!templatesDict[currentTemplate].includes(normalizedSelectedField)) {
        templatesDict[currentTemplate].push(normalizedSelectedField);
        loadTemplateFields(currentTemplate, from_field=true); // Reload the template fields
        hasChanges = true;
        document.getElementById('save-fields-btn').style.display = 'inline-block';
        document.getElementById('revert-fields-btn').style.display = 'inline-block';
    } else {
        alert("Field already exists in the template.");
    }

    closeFieldPopup();
}

function closeFieldPopup() {
    document.getElementById("field-popup").style.display = "none";
}

module.exports = {
    saveTemplateChanges: saveTemplateChanges,
    delete_template: delete_template,
    revertTemplateChanges: revertTemplateChanges,
    confirmDeleteField: confirmDeleteField,
    addNewField: addNewField,
    deleteField: deleteField,
  };
 