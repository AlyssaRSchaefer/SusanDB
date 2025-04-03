const urlParams = new URLSearchParams(window.location.search);
const studentId = urlParams.get('id');

document.addEventListener("DOMContentLoaded", function () {
    if (studentId) {
        console.log(studentId);
        document.getElementById("student-id").value = studentId;
    }
});

document.getElementById('file-upload').addEventListener('change', function () {
    const fileName = this.files[0] ? this.files[0].name : "No file selected";
    document.getElementById('file-name').textContent = fileName;
});

