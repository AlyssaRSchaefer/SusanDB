document.getElementById('file-upload').addEventListener('change', function () {
    const fileName = this.files[0] ? this.files[0].name : "No file selected";
    document.getElementById('file-name').textContent = fileName;
});


function handleFileUpload() {
    const fileInput = document.getElementById('file-upload');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file first!');
        return;
    }

    if (!/\.(xlsx|xls)$/i.test(file.name)) {
        alert('Invalid file type. Please upload an Excel file.');
        return;
    }

    // Trigger form submission to Flask
    document.getElementById('upload-form').submit();
}

