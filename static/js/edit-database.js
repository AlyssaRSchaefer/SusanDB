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

function getAllFields(){
    fetch('/get_student_fields')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            fields = data; // Store result in the `fields` array
            console.log("Fields loaded:", fields); // Debugging log
        })
        .catch(error => {
            console.error("Error loading fields:", error);
        });
}

window.onload = () => {
    getAllFields()
};
