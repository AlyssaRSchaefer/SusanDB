let fields = []

function fetchLayout() {

    const table = document.getElementById('layout-fields-body');
    fields = [];

    fetch('/get_fields')
    .then(response => response.json())
    .then(data => {
        table.innerHTML = '';

        data.forEach(field => {
            const tr = document.createElement("tr");
            tr.id = "layout" + field;
            tr.classList.add("template-selectable-row")
            tr.innerHTML = "<td><span class='template-name'>" + field.replace("_", " ").toUpperCase() + "</span><span class='templates-delete-icon'>🗑️</span></td>";
            table.appendChild(tr);
            fields.push(field);
        })
    })
    .catch(error => console.error('Error:', error));
}

window.onload = () => {
    fetchLayout();
};