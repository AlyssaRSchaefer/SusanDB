let fields = []

function generateErrorMessage(msg, container){

}

function addNewField() {
    let name = document.getElementById("add-field-name").value;
    let defaultValue = document.getElementById("add-field-default").value;
    let addToLayout = document.getElementById("add-field-layout").checked;

    if (name.length === 0) {
        generateErrorMessage("The name of the new field cannot be blank.", "add-field-error-msg");
        return;
    }

    if (fields.includes(name)) {
        generateErrorMessage("The database already contains a field with this name.", "add-field-error-msg");
        return;
    }

    fetch('/add_field_to_db', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            field: name,
            default: defaultValue,
            addToLayout: addToLayout
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json(); // Ensure response is processed
    })
    .catch(error => console.error('Error:', error));
}

function deleteField(){
    let field = document.getElementById("delete-field-select").value;
    fetch('/delete_field_from_db', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ field: field })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw new Error(err.error || "Failed to delete field."); });
        }
        return response.json();
    })
    .then(data => {
        console.log("Success:", data.message);
        alert("Field deleted successfully.");
        getAllFields(); // Refresh the field list after deletion
    })
    .catch(error => {
        console.error("Error:", error);
        alert(`Error deleting field: ${error.message}`);
    });
}

function getAllFields() {
    return fetch('/get_student_fields')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            fields = data;
            console.log("Fields loaded:", fields);
        })
        .catch(error => {
            console.error("Error loading fields:", error);
        });
}

window.onload = () => {
    getAllFields().then(() => {
        if (document.getElementById("delete-field-select")) {
            populateDeleteFieldSelect();
        }
    });
};


function populateDeleteFieldSelect() {
    let select = document.getElementById("delete-field-select");

    select.innerHTML = "";

    let placeholder = document.createElement("option");
    placeholder.textContent = "Select a field to delete";
    placeholder.value = "";
    select.appendChild(placeholder);

    fields.forEach(field => {
        let option = document.createElement("option");
        option.value = field;  
        option.textContent = field.toUpperCase().replaceAll("_", " "); 
        select.appendChild(option);
    });
}

window.onload = () => {
    getAllFields().then(() => {
        if (document.getElementById("delete-field-select")) {
            populateDeleteFieldSelect();
        }
    });
};
