let params = (new URL(document.location)).searchParams;
let person_id = params.get('person_id');

function loadAppearancesTable(appearances) {
    const table = document.getElementById("appearances");
    appearances.forEach( appearance => {
        let row = table.insertRow();
        let date = row.insertCell(0);
        date.innerHTML = "";
        let name = row.insertCell(1);
        name.innerHTML = appearance;
        let role = row.insertCell(2);
        role.innerHTML = "";
    });
  };

function loadPersonData(person) {

    console.log(person)

    //Name
    if('name_prefix' in person){
        var name_prefix = person['name_prefix']
    }

    if('name_first' in person){
        var name_first = person['name_first']
    }

    if('name_nickname' in person){
        let name_nickname_raw = person['name_nickname']
        var name_nickname = ['"', name_nickname_raw, '"'].join('')
    }

    if('name_middle' in person){
        var name_middle = person['name_middle']
    }

    if('name_last' in person){
        var name_last = person['name_last']
    }

    if('name_suffix' in person){
        var name_suffix = person['name_suffix']
    }

    //let name_full = name_prefix + name_first + name_nickname + name_middle + name_last + name_suffix
    let name_full = [name_prefix , " " , name_first , " " , name_nickname, " " , name_middle , " " , name_last , " " , name_suffix].join('')
    let name_display = [name_first , " " , name_nickname, " " , name_last].join('')

    document.getElementById("name_full").innerHTML = name_full;
    document.getElementById("name_display").innerHTML = name_display;

    //Dates
    if('date_birth' in person) {
        document.getElementById("date_birth").innerHTML = person['date_birth'];
    } else {
        document.getElementById("date_birth").style.display = "none";
        document.getElementById("date_birth_header").style.display = "none";
    }



    if('date_death' in person) {
        document.getElementById("date_death").innerHTML = person['date_death'];
    } else {
        document.getElementById("date_death").style.display = "none";
        document.getElementById("date_death_header").style.display = "none";
    }

    //Descriptions
    if('desc_brief' in person) {
        document.getElementById("desc_brief").innerHTML = person['desc_brief'];
    } else {
        document.getElementById("desc_brief").style.display = "none";
        document.getElementById("desc_brief_card").style.display = "none";
        document.getElementById("desc_brief_shadow").style.display = "none";

    }

    if('desc_full' in person) {
        document.getElementById("desc_full").innerHTML = person['desc_full'];
    } else {
        document.getElementById("desc_full").style.display = "none";
        document.getElementById("desc_full_header").style.display = "none";
    }
 
    //Roles
    if('role' in person) {
        let roles = person['role']
        let proper_roles = []
        for(role in roles){
            proper_roles[role] = roles[role].charAt(0).toUpperCase() + roles[role].slice(1);
        }
        let role_string = proper_roles.join(', ')
        document.getElementById("roles").innerHTML = role_string;
    } else {
        document.getElementById("roles").style.display = "none";
        document.getElementById("roles_header").style.display = "none";
    }

    //Appearances
    if('appearances' in person) {
        loadAppearancesTable(person['appearances'])
    } else {
        loadAppearancesTable(['No appearances recorded.'])
    }

    //Person ID
    document.getElementById("person_id").innerHTML = person['person_id'];

}


//Clear Appearances table before filling
var table = document.getElementById("appearances");
for(var i = 1;i<table.rows.length;){
    table.deleteRow(i);
}

fetch('ingest_api/person?person_id=' + person_id)
.then((response) => response.json())
.then((data) => loadPersonData(data));