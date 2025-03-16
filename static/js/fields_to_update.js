// Variable to hold the selected fields
let selectedFields = [];

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

function toggleSelectAll() {
    let checkboxes = document.querySelectorAll('.fields-to-update-checkbox');
    let selectAllCheckbox = document.getElementById('selectAllCheckbox');

    // Update each checkbox based on the state of the "Select All" checkbox
    checkboxes.forEach(checkbox => checkbox.checked = selectAllCheckbox.checked);
}
