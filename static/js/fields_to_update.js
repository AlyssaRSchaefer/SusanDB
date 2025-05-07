// Variable to hold the selected fields
let selectedExcelFields = [];
let selectedSusanDBFields = [];
let mappingRules = [];
let previewUpdates = [];
let newStudents = [];

const dataHolder = document.getElementById('data-holder');
const columns = JSON.parse(dataHolder.getAttribute('data-columns'));
const susandbColumns = JSON.parse(dataHolder.getAttribute('data-susandb-columns'));


// STEP 1
// Function to collect selected fields and switch to the second popup
function submitFieldsToUpdate() {
    // Collect all the selected checkboxes
    const checkboxes = document.querySelectorAll('.fields-to-update-checkbox:checked');
    
    // Store the values of the selected checkboxes into the array
    selectedExcelFields = Array.from(checkboxes).map(checkbox => checkbox.value);
    
    if (selectedExcelFields.length === 0) {
        alert('Please select at least one field!');
        return;
    }
    
    document.getElementById('fields-to-update').style.display = 'none';
    
    document.getElementById('choose-mapping-key').style.display = 'flex';
}

// STEP 2
// Function to handle the submission of selected primary keys (in both tables)
function submitPrimaryKeys() {
    // Optionally, proceed with the next steps after submitting
    fillMapDataTable();
    document.getElementById('choose-mapping-key').style.display = 'none';
    document.getElementById('map-data').style.display = 'flex';
}

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

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById("select-all-checkbox").addEventListener("change", function () {
        const checked = this.checked;
        document.querySelectorAll("#preview-table-body input[type='checkbox']").forEach(checkbox => {
            checkbox.checked = checked;
        });
    });

    document.getElementById("select-all-new").addEventListener("change", function () {
        const checked = this.checked;
        document.querySelectorAll("#new-students-table-body input[type='checkbox']").forEach(checkbox => {
            checkbox.checked = checked;
        });
    });
    
    const excelSide = document.querySelector('.excel-side');
    const susandbSide = document.querySelector('.susandb-side');
    const addRuleButton = document.querySelector('.add-rule-button');
    const rulesBody = document.getElementById('rules-body');
    const confirmButton = document.getElementById('map-key-confirm-button');

    // Function to add a new dropdown and (+) button
    function addDropdown(side, type) {
        const newDropdown = document.createElement('select');
        newDropdown.className = `${type}-field-select select-import select`;
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
        addRuleButton.style.display = addRuleButton.disabled ? "none" : "table-cell";
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
            // Store the mapping rule
            mappingRules.push({
                excel: excelValues,
                susandb: susandbValues
            });
            console.log("Mapping Rules:", mappingRules); // Log the mapping rules

            const newRow = document.createElement('tr');
            newRow.innerHTML = `
                <td>${excelValues.join(' + ')}</td>
                <td style="width: 3ch; text-align: center;">=</td>
                <td>${susandbValues.join(' + ')}</td>
            `;
            rulesBody.prepend(newRow);
            // Show the Confirm button if it's the first rule
            if (rulesBody.children.length == 2) {
                confirmButton.style.display = 'block';
            }

            // Clear the rule builder
            excelSide.innerHTML = `
                <select class="excel-field-select select">
                    <option value="">Select Excel Field</option>
                    ${columns.map(column => `<option value="${column}">${column}</option>`).join('')}
                </select>
                <button class="add-excel-button" style="display: none;">+</button>
            `;
            susandbSide.innerHTML = `
                <select class="susandb-field-select select">
                    <option value="">Select SusanDB Field</option>
                    ${susandbColumns.map(column => `<option value="${column}">${column}</option>`).join('')}
                </select>
                <button class="add-susandb-button" style="display: none;">+</button>
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
            addRuleButton.style.display="none";
        }
    });
});

// STEP 3
// Map data
// Function to fill the map-data table with selectedExcelFields and dropdowns
function fillMapDataTable() {
    const tableBody = document.querySelector('#map-data .import-table tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    selectedExcelFields.forEach(field => {
        const newRow = document.createElement('tr');
        newRow.innerHTML = `
            <td>${field}</td>
            <td>
                <select class="susandb-map-select select-import select unselected"></select>
            </td>
        `;
        tableBody.appendChild(newRow);

        const dropdown = newRow.querySelector('.susandb-map-select');
        populateDropdown(dropdown, susandbColumns);

        // Add event listener to the dropdown
        dropdown.addEventListener('change', function () {
            checkSubmitButton();
            if (this.value) {
                dropdown.classList.remove('unselected');
                dropdown.classList.add('import-selected');
            } else {
                dropdown.classList.add('unselected');
                dropdown.classList.remove('import-selected');
            }
        });
    });

    document.getElementById('map-data').style.display = 'flex'; // Show the table
    checkSubmitButton();
}

function checkSubmitButton() {
    const dropdowns = document.querySelectorAll('.susandb-map-select');
    const submitButton = document.getElementById('submit-mapping-data-btn');
    let allSelected = true;

    dropdowns.forEach(dropdown => {
        if (!dropdown.value) { // Check if any dropdown is empty
            allSelected = false;
        }
    });

    if (allSelected) {
        submitButton.style.display = 'block';
    } else {
        submitButton.style.display = 'none';
    }
}

function submitMappingData() {
    selectedSusanDBFields = []; // Reset before updating

    const selectElements = document.querySelectorAll("#map-data tbody select");

    selectElements.forEach(select => {
        if (select.value) {
            selectedSusanDBFields.push(select.value);
        }
    });

    console.log(selectedSusanDBFields);
    console.log(selectedExcelFields);

    fetch('/generate_preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            selectedExcelFields: selectedExcelFields,
            selectedSusanDBFields: selectedSusanDBFields,
            mappingRules: mappingRules
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Error generating preview: " + data.error);
        } else {
            previewUpdates = data.preview
            newStudents = data.new_students;
            if(data.change_applied) {
                displayPreviewTable(data.preview);  // Call function to show updates
            } else {
                // Get the <tbody> and inject a single “None” row
                const body = document.getElementById("preview-table-body");
                body.innerHTML = `
                    <tr>
                    <td colspan="5" style="text-align: center; opacity: 0.7;">
                        None
                    </td>
                    </tr>
                `;
            }
            if (data.new_students.length != 0) {
                displayNewStudentsTable(data.new_students); // Call function to show new students
            } else {
                document.getElementById("new-students-table-container").style.display = "none";
            }
            if(!data.change_applied && data.new_students.length == 0) {
                alert("No changes detected in the selected fields.");
                window.location.href = "/database";
            }
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        alert('An error occurred while generating preview.');
    });
}

function displayPreviewTable(previewUpdates) {
    const tableBody = document.getElementById("preview-table-body");
    tableBody.innerHTML = "";

    previewUpdates.forEach((update, studentIndex) => {
        let hasChanges = false;
        let rowContent = `
            <tr>
                <td>${update.student_id}</td>
                <td>${update.first_name}</td>
                <td>${update.last_name}</td>
                <td>
        `;

        update.changes.forEach(change => {
            const isUnchanged = change.unchanged;

            rowContent += `<strong>${change.field}:</strong> 
                <span style="color: ${isUnchanged ? '#aaa' : '#d9534f'}">
                    ${change.current_value}
                </span>
                <strong> → </strong> 
                <span style="color: ${isUnchanged ? '#aaa' : '#5cb85c'}">
                    ${change.new_value}
                </span><br>`;

            if (!isUnchanged) hasChanges = true;
        });

        rowContent += `</td>`;

        if (hasChanges) {
            rowContent += `
                <td>
                    <input type="checkbox" class="update-checkbox" 
                        data-student-index="${studentIndex}">
                </td>
            `;
        } else {
            rowContent += `<td style="opacity: 0.7; text-align: center;">—</td>`;
        }

        rowContent += `</tr>`;
        tableBody.innerHTML += rowContent;
    });

    document.getElementById("confirm-update-section").style.display = "flex";
    document.getElementById("map-data").style.display = "none";
}

function displayNewStudentsTable(newStudents) {
    const tableBody = document.getElementById("new-students-table-body");
    tableBody.innerHTML = "";
  
    newStudents.forEach((student, idx) => {
      // Build a little HTML block for the raw_values map
      let rawHtml = "";
      for (const [field, val] of Object.entries(student.raw_values)) {
        rawHtml += `<strong>${field}:</strong> ${val}<br>`;
      }
  
      // Each row gets a checkbox so the user can pick which new students to insert
      const rowHtml = `
        <tr>
          <td>${student.student_id}</td>
          <td>${student.first_name}</td>
          <td>${student.last_name}</td>
          <td>${rawHtml}</td>
          <td style="text-align: center;">
            <input type="checkbox"
                   class="new-student-checkbox"
                   data-new-index="${idx}">
          </td>
        </tr>
      `;
      tableBody.innerHTML += rowHtml;
    });
    document.getElementById("confirm-update-section").style.display = "flex";
    document.getElementById("map-data").style.display = "none";
}  



document.getElementById("finalSubmitButton").addEventListener("click", function() {
    // 1) Collect selected updates
    const selectedUpdates = Array.from(
      document.querySelectorAll(".update-checkbox:checked")
    ).map(cb => {
      const idx = parseInt(cb.getAttribute("data-student-index"), 10);
      return previewUpdates[idx];
    });
  
    // 2) Collect selected new students
    const selectedNew = Array.from(
      document.querySelectorAll(".new-student-checkbox:checked")
    ).map(cb => {
      const idx = parseInt(cb.getAttribute("data-new-index"), 10);
      return newStudents[idx];
    });
  
    // 3) Require at least one
    if (selectedUpdates.length === 0 && selectedNew.length === 0) {
      alert("No changes or new students selected.");
      return;
    }
  
    // 4) Send both arrays together
    fetch('/update_db_from_excel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        updates:      selectedUpdates,
        new_students: selectedNew
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert("Error updating database: " + data.error);
      } else {
        alert(data.message);
        window.location.href = "/database";
      }
    })
    .catch(error => {
      console.error('Fetch error:', error);
      alert('An error occurred while updating the database. Please try again.');
    });
  });
  

function toggleSelectAll() {
    let checkboxes = document.querySelectorAll('.fields-to-update-checkbox');
    let selectAllCheckbox = document.getElementById('selectAllCheckbox');

    // Update each checkbox based on the state of the "Select All" checkbox
    checkboxes.forEach(checkbox => checkbox.checked = selectAllCheckbox.checked);
}
