let params = (new URL(document.location)).searchParams;
let transfer_id = params.get('transfer_id');

function loadFilesTable(files) {
    const table = document.getElementById("files_table");
    files.forEach( file => {
        let row = table.insertRow();
        let file_name = row.insertCell(0);
        file_name.innerHTML = file.file_name;
    });
  };

  function loadErrorsTable(errors) {
    const table = document.getElementById("errors_table");
    errors.forEach( error => {
        let row = table.insertRow();

        let file = row.insertCell(0);
        file.innerHTML = error.file_name;

        let source = row.insertCell(1);
        source.innerHTML = error.source;

        let error_text = row.insertCell(2);
        error_text.innerHTML = error.error;

        let time = row.insertCell(3);
        time.innerHTML = error.time;
    });
  };


function loadTransferData(transfer) {

    console.log(transfer)

    //Name
    if('name' in transfer) {
        document.getElementById("name").innerHTML = transfer['name'];
    } else {
        document.getElementById("name").style.display = "none";
        document.getElementById("name_header").style.display = "none";
    }

    //Status
    if('status' in transfer) {
        document.getElementById("status").innerHTML = transfer['status'];
    } else {
        document.getElementById("status").style.display = "none";
        document.getElementById("status_header").style.display = "none";
    }

    //Type
    if('type' in transfer) {
        document.getElementById("type").innerHTML = transfer['type'];
    } else {
        document.getElementById("type").style.display = "none";
        document.getElementById("type_header").style.display = "none";
    }

    //Init. Time
    if('init_time' in transfer) {
        document.getElementById("init_time").innerHTML = transfer['init_time'];
    } else {
        document.getElementById("init_time").style.display = "none";
        document.getElementById("init_time_header").style.display = "none";
    }

    //Files
    if('files' in transfer) {
        loadFilesTable(transfer['files'])
    } else {
        loadFilesTable(['No files transferred.'])
    }

    //Errors
    if('errors' in transfer) {
        loadErrorsTable(transfer['errors'])
    } else {
        document.getElementById("errors_card").style.display = "none";
    }

    //Transfer ID
    document.getElementById("transfer_id").innerHTML = transfer['transfer_id'];

}


//Clear tables before filling

var table = document.getElementById("files_table");
for(var i = 1;i<table.rows.length;){
    table.deleteRow(i);
}

var table = document.getElementById("errors_table");
for(var i = 1;i<table.rows.length;){
    table.deleteRow(i);
}

fetch('ingest_api/transfer?transfer_id=' + transfer_id)
.then((response) => response.json())
.then((data) => loadTransferData(data));