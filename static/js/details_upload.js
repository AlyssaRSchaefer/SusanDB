let student_id = "-1"; 
document.addEventListener("DOMContentLoaded", function() {
    console.log("window.location.search:", window.location.search);  //log the entire query string
    const urlParams = new URLSearchParams(window.location.search);
    const id = urlParams.get('id');
    student_id = id; 
    console.log("Extracted Student ID:", id);  //debugging log

    //file input change handler
    document.getElementById('file-upload').addEventListener('change', function () {
        const fileName = this.files[0] ? this.files[0].name : "No file selected";
        document.getElementById('file-name').textContent = fileName;
    });
}); 

function uploadToOnedrive() 
{
    const fileInput = document.getElementById("file-upload");
    const id = student_id; 
    console.log(`1): ID before type conversion: ${id}`);
    //check if id exists and is valid
    if (!id || isNaN(id)) {
        alert("Student ID is missing or invalid. Unable to proceed.");
        return;
    }
    console.log(`ID before type conversion: ${id}`); 
    const studentID = Number(id);  //convert to number
    const file = fileInput.files[0];
    
    if (!file) {
        alert("Please select a file to upload.");
        return;
    }

    console.log(`Student id = ${studentID}`); 
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("student_id", studentID);
    console.log(`Formdata:\nfile: ${file}, student_id:${studentID}`)
    fetch('/upload_student_files', 
    {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => 
    {
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            alert("File uploaded successfully.");
            fileInput.value = "";  // Clear file input
            document.getElementById('file-name').textContent = "No file selected";  // Reset display
        }
    })
    .catch(error => 
    {
        console.error("Upload Error:", error);
        alert("An error occurred while uploading the file.");
    });
}