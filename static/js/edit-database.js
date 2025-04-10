let fields = []

function generateErrorMessage(msg){
    alert(msg);
}

function addNewField() {
    loading.style.display = "flex";
    let name = document.getElementById("add-field-name").value.replaceAll(" ", "_");
    let defaultValue = document.getElementById("add-field-default").value;
    let addToLayout = document.getElementById("add-field-layout").checked;

    if (name.length === 0) {
        generateErrorMessage("The name of the new field cannot be blank.");
        loading.style.display = "none";
        return;
    }

    if (fields.includes(name)) {
        generateErrorMessage("The database already contains a field with this name.");
        loading.style.display = "none";
        return;
    }

    clearAddFieldForm(); // You can still clear early

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
        return response.json();
    })
    .then(data => {
        openFieldPopup();              
        loading.style.display = "none"; 
    })
    .catch(error => {
        console.error('Error:', error);
        generateErrorMessage("There was an error adding the new field.");
        loading.style.display = "none"; // Still hide it on error
    });
}


function deleteField() {
    let field = document.getElementById("delete-field-select").value;

    if (field == "") {
        generateErrorMessage("Please choose a valid field.");
        return;
    }

    loading.style.display = "flex"; // Show loading while request is in progress

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
        removeFieldFromSelect(field);  
        openFieldPopup();              
        loading.style.display = "none";
    })
    .catch(error => {
        console.error("Error:", error);
        alert(`Error deleting field: ${error.message}`);
        loading.style.display = "none";
    });
}


function addStudent(){
    loading.style.display = "flex";
    document.getElementById("add-student-form").submit();
}

function openFieldPopup() {
    document.getElementById("field-popup").style.display = "flex";
}

function closeFieldPopup() {
    document.getElementById("field-popup").style.display = "none";
}

function clearAddFieldForm(){
    document.getElementById("add-field-name").value="";
    document.getElementById("add-field-default").value="";
    document.getElementById("add-field-layout").checked = false;
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

function removeFieldFromSelect(field) {
    let select = document.getElementById("delete-field-select");
    let optionToRemove = select.querySelector(`option[value="${field}"]`);
    if (optionToRemove) {
        select.removeChild(optionToRemove);
    }
}

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

function populateAddStudentForm(){
    let form = document.getElementById("add-student-form");
    form.innerHTML = "";
    fields.forEach(field => {
        let textInput = document.createElement("input");
        textInput.classList.add("text-input");
        textInput.name = field;
        textInput.type = "text";
        textInput.placeholder = field.toUpperCase().replaceAll("_", " ");
        form.append(textInput);
        form.append(document.createElement("br"));
    })
}

window.onload = () => {
    getAllFields().then(() => {
        if (document.getElementById("delete-field-select")) {
            populateDeleteFieldSelect();
        }
        else if (document.getElementById("add-student-form")){
            populateAddStudentForm();
        }
    });
};
