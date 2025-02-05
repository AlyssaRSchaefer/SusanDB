sort = {}
let columns = [];

function sortTableByField(field){
    let iconID = "database-icon-" + field;
    let icon = document.getElementById(iconID);
    icon.style.display = "inline";

    let columnHeader = document.getElementById(field);
    columnHeader.style.backgroundColor = "var(--secondary-color-highlight)";

    sort[field] = "ASC";
    fetchData(sort);
    
}

function fetchColumns() {
    const tableHeader = document.querySelector('table thead');

    fetch('/get_fields')
    .then(response => response.json())
    .then(data => {
        tableHeader.innerHTML = '';

        data.forEach(field => {
            const th = document.createElement("th");
            th.id = field;
            th.classList.add("database-column-name");
            th.onclick = () => sortTableByField(field);
            th.innerHTML = field.replace("_", " ").toUpperCase() + '<img id="database-icon-' + field + '" class="database-sort-icon" src="static/icons/icon-up.png" alt="Sort icon"></img>';
            tableHeader.appendChild(th);
            columns.push(field);
        });
        td.onclick = () => sortTableByField(field);

    })
    .catch(error => console.error('Error:', error));
}


function fetchData(sort = { name: 'ASC' }) {
    const table = document.querySelector('table tbody'); // Assuming you want to append rows to the tbody

    fetch('/get_data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ sort: sort })
    })
    .then(response => response.json())
    .then(data => {
        table.innerHTML = '';
        data.forEach(row => {
            const tr = document.createElement("tr");


            // Loop through columns to ensure correct order
            columns.forEach(col => {
                const td = document.createElement("td");
                td.innerHTML = row[col] !== undefined ? row[col] : ''; // Handle missing fields
                tr.appendChild(td);
            });

            table.appendChild(tr);
        });
    })
    .catch(error => console.error('Error:', error));
}

window.onload = () => {
    fetchColumns();
    fetchData();
};
