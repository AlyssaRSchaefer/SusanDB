const urlParams = new URLSearchParams(window.location.search);
const id = urlParams.get('id');

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

    // Trigger form submission to Flask
    document.getElementById('upload-form').submit();
}