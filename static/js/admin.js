const saveButton = document.getElementById("admin-save-button");
const colorSchemeSelect = document.getElementById("admin-color-select");
const exportButton = document.getElementById("excel-export-button")

colorSchemeSelect.addEventListener("change", function() {
    document.body.className = this.value;
    displaySaveButton();
});

function displaySaveButton() {
    saveButton.style.display = "flex";
}

function saveColorScheme() {
    loading.style.display = "flex";
    let colorScheme = colorSchemeSelect.value;
    saveButton.style.display = "none";

    fetch("/update_color_scheme", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ colorScheme: colorScheme })
    })
    .then(response => response.json())
    .then(() => loading.style.display = "none")
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

function exportToExcel()
{
    fetch("/export_to_excel")
    .then(response => {
        if (!response.ok) throw new Error("Network response was not ok");

        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "students.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => {
        console.error("Export failed:", error);
    });
}

window.onload = () => {
    fetchColorScheme();
};

