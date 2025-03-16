// Variable to hold the selected fields
let selectedFields = [];
let primaryKeys = {}

// STEP 1
// Function to collect selected fields and switch to the second popup
function submitFieldsToUpdate() {
    // Collect all the selected checkboxes
    const checkboxes = document.querySelectorAll('.fields-to-update-checkbox:checked');
    
    // Store the values of the selected checkboxes into the array
    selectedFields = Array.from(checkboxes).map(checkbox => checkbox.value);
    
    if (selectedFields.length === 0) {
        alert('Please select at least one field!');
        return;
    }
    
    document.getElementById('fields-to-update').style.display = 'none';
    
    document.getElementById('choose-mapping-key').style.display = 'flex';
}

// STEP 2
// Function to handle the submission of selected primary keys (in both tables)
function submitPrimaryKeys() {
    // Get selected Excel fields
    const selectedExcelFields = Array.from(document.querySelectorAll('.excel-fields-checkbox:checked')).map(checkbox => checkbox.value);

    // Get selected SusanDB fields
    const selectedSusanDBFields = Array.from(document.querySelectorAll('.susandb-fields-checkbox:checked')).map(checkbox => checkbox.value);

    // Store the selected fields in the primaryKeys dictionary
    primaryKeys = {
        excelFields: selectedExcelFields,
        susandbFields: selectedSusanDBFields,
    };

    console.log(primaryKeys); // Log the primaryKeys dictionary to check the data

    // Optionally, proceed with the next steps after submitting
    document.getElementById('choose-mapping-key').style.display = 'none';
    document.getElementById('confirm-mapping-key').style.display = 'flex';
}

// STEP 3

function toggleSelectAll() {
    let checkboxes = document.querySelectorAll('.fields-to-update-checkbox');
    let selectAllCheckbox = document.getElementById('selectAllCheckbox');

    // Update each checkbox based on the state of the "Select All" checkbox
    checkboxes.forEach(checkbox => checkbox.checked = selectAllCheckbox.checked);
}
