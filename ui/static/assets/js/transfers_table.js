function loadTableData(items) {
    const table = document.getElementById("dataTable");
    items.forEach( item => {
        let row = table.insertRow();
        let name = row.insertCell(0);

        var link = document.createElement("a");
        link.href = "../transfer?transfer_id=" + item.transfer_id;
        link.innerHTML = item.name;
        name.appendChild(link);

        let transfer_id = row.insertCell(1);
        transfer_id.innerHTML = item.transfer_id;
        let type = row.insertCell(2);
        type.innerHTML = item.type;
        let init_time = row.insertCell(3);
        init_time.innerHTML = item.init_time;
        let status = row.insertCell(4);
        status.innerHTML = item.status;
    });
  };


function refreshTable() {


    var table = document.getElementById("dataTable");
    for(var i = 1;i<table.rows.length;){
        table.deleteRow(i);
    }

    fetch('ingest_api/transfers')
    .then((response) => response.json())
    .then((data) => loadTableData(data));

    setTimeout(refreshTable, 60000);
}


refreshTable();