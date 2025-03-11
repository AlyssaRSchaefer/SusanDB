const saveButton = document.getElementById("admin-save-button");
const colorSchemeSelect = document.getElementById("admin-color-select");

colorSchemeSelect.addEventListener("change", function() {
    document.body.className = this.value;
    displaySaveButton();
});

function displaySaveButton() {
    saveButton.style.display = "flex";
}

function saveColorScheme() {
    let colorScheme = colorSchemeSelect.value;
    saveButton.style.display = "none";

    fetch("/update_color_scheme", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ colorScheme: colorScheme })
    })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error("Error:", error));
}

function fetchColorScheme() {
    fetch("/get_color_scheme_session")
        .then(response => response.json())
        .then(data => {
            // Set the selected value of the color scheme dropdown
            colorSchemeSelect.value = data.color_scheme;
        })
        .catch(error => console.error("Error:", error));
}

window.onload = () => {
    fetchColorScheme();
};
