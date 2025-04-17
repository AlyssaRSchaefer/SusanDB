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

/*
function exportToExcel() {
    if (window.pywebview) {
        window.pywebview.api.export_to_excel().then(function(message) {
            alert(message);
        }).catch(function(error) {
            console.error("Export failed:", error);
        });
    } else {
        alert("This feature is only available in the desktop app.");
    }
}
*/ 

window.onload = () => {
    fetchColorScheme();
};

document.getElementById("revert-button").onclick = async function () {
    const confirmed = confirm("Are you sure you want to revert to the last logout? This will overwrite current student data.");
    if (!confirmed) return;

    loading.style.display = "flex";

    const response = await fetch("/revert", { method: "POST" });
    const result = await response.json();
    
    if (result.success) {
        loading.style.display = "none";
        alert("Database reverted successfully.");
    } else {
        loading.style.display = "none";
        alert("No changes were made.");
    }
};

