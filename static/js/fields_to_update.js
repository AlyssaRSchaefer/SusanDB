// Variable to hold the selected fields
let selectedFields = [];
let primaryKeys = {};

const dataHolder = document.getElementById('data-holder');
const columns = JSON.parse(dataHolder.getAttribute('data-columns'));
const susandbColumns = JSON.parse(dataHolder.getAttribute('data-susandb-columns'));


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

document.addEventListener('DOMContentLoaded', function () {
    const excelSide = document.querySelector('.excel-side');
    const susandbSide = document.querySelector('.susandb-side');
    const addRuleButton = document.querySelector('.add-rule-button');
    const rulesBody = document.getElementById('rules-body');
    const confirmButton = document.querySelector('.confirm-button');

    // Function to populate a dropdown with options
    function populateDropdown(dropdown, options) {
        dropdown.innerHTML = '<option value="">Select ' + (dropdown.classList.contains('excel-field-select') ? 'Excel' : 'SusanDB' + ' Field</option>');
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            dropdown.appendChild(optionElement);
        });
    }

    // Function to add a new dropdown and (+) button
    function addDropdown(side, type) {
        const newDropdown = document.createElement('select');
        newDropdown.className = `${type}-field-select select-import`;
        populateDropdown(newDropdown, type === 'excel' ? columns : susandbColumns);

        const newPlusButton = document.createElement('button');
        newPlusButton.className = `add-${type}-button`;
        newPlusButton.textContent = '(+)';
        newPlusButton.style.display = 'none';

        side.appendChild(newDropdown);
        side.appendChild(newPlusButton);

        // Add event listener to the new dropdown
        newDropdown.addEventListener('change', function () {
            if (this.value) {
                newPlusButton.style.display = 'inline-block';
            } else {
                newPlusButton.style.display = 'none';
            }
            checkAddRuleButton();
        });

        // Add event listener to the new (+) button
        newPlusButton.addEventListener('click', function () {
            addDropdown(side, type);
        });
    }

    // Function to check if the "Add Rule" button should be enabled
    function checkAddRuleButton() {
        const excelFields = excelSide.querySelectorAll('.excel-field-select');
        const susandbFields = susandbSide.querySelectorAll('.susandb-field-select');

        let excelFilled = false;
        let susandbFilled = false;

        excelFields.forEach(select => {
            if (select.value) excelFilled = true;
        });

        susandbFields.forEach(select => {
            if (select.value) susandbFilled = true;
        });

        addRuleButton.disabled = !(excelFilled && susandbFilled);
    }

    // Add initial event listeners
    excelSide.querySelector('.excel-field-select').addEventListener('change', function () {
        if (this.value) {
            excelSide.querySelector('.add-excel-button').style.display = 'inline-block';
        } else {
            excelSide.querySelector('.add-excel-button').style.display = 'none';
        }
        checkAddRuleButton();
    });

    susandbSide.querySelector('.susandb-field-select').addEventListener('change', function () {
        if (this.value) {
            susandbSide.querySelector('.add-susandb-button').style.display = 'inline-block';
        } else {
            susandbSide.querySelector('.add-susandb-button').style.display = 'none';
        }
        checkAddRuleButton();
    });

    excelSide.querySelector('.add-excel-button').addEventListener('click', function () {
        addDropdown(excelSide, 'excel');
    });

    susandbSide.querySelector('.add-susandb-button').addEventListener('click', function () {
        addDropdown(susandbSide, 'susandb');
    });

    // Add Rule Button Logic
    addRuleButton.addEventListener('click', function () {
        const excelFields = excelSide.querySelectorAll('.excel-field-select');
        const susandbFields = susandbSide.querySelectorAll('.susandb-field-select');

        const excelValues = Array.from(excelFields).map(select => select.value).filter(Boolean);
        const susandbValues = Array.from(susandbFields).map(select => select.value).filter(Boolean);

        if (excelValues.length > 0 && susandbValues.length > 0) {
            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>${excelValues.join(', ')}</td>
                <td>${susandbValues.join(', ')}</td>
            `;
            rulesBody.appendChild(newRow);

            // Show the Confirm button if it's the first rule
            if (rulesBody.children.length === 1) {
                confirmButton.style.display = 'block';
            }

            // Clear the rule builder
            excelSide.innerHTML = `
                <select class="excel-field-select select">
                    <option value="">Select Excel Field</option>
                    ${columns.map(column => `<option value="${column}">${column}</option>`).join('')}
                </select>
                <button class="add-excel-button" style="display: none;">(+)</button>
            `;
            susandbSide.innerHTML = `
                <select class="susandb-field-select select">
                    <option value="">Select SusanDB Field</option>
                    ${susandbColumns.map(column => `<option value="${column}">${column}</option>`).join('')}
                </select>
                <button class="add-susandb-button" style="display: none;">(+)</button>
            `;

            // Reattach event listeners
            excelSide.querySelector('.excel-field-select').addEventListener('change', function () {
                if (this.value) {
                    excelSide.querySelector('.add-excel-button').style.display = 'inline-block';
                } else {
                    excelSide.querySelector('.add-excel-button').style.display = 'none';
                }
                checkAddRuleButton();
            });

            susandbSide.querySelector('.susandb-field-select').addEventListener('change', function () {
                if (this.value) {
                    susandbSide.querySelector('.add-susandb-button').style.display = 'inline-block';
                } else {
                    susandbSide.querySelector('.add-susandb-button').style.display = 'none';
                }
                checkAddRuleButton();
            });

            excelSide.querySelector('.add-excel-button').addEventListener('click', function () {
                addDropdown(excelSide, 'excel');
            });

            susandbSide.querySelector('.add-susandb-button').addEventListener('click', function () {
                addDropdown(susandbSide, 'susandb');
            });

            addRuleButton.disabled = true;
        }
    });
});
// STEP 3

function toggleSelectAll() {
    let checkboxes = document.querySelectorAll('.fields-to-update-checkbox');
    let selectAllCheckbox = document.getElementById('selectAllCheckbox');

    // Update each checkbox based on the state of the "Select All" checkbox
    checkboxes.forEach(checkbox => checkbox.checked = selectAllCheckbox.checked);
}
