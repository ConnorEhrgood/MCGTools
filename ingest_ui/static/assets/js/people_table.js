function paginate(data, itemsPerPage) {
    var pages = [];
    for (var i = 0; i < data.length; i += itemsPerPage) {
        pages.push(data.slice(i, i + itemsPerPage));
    }
    return pages;
}

function clearPagination(tableId) {
    var pagination = document.getElementById(tableId + "-pagination");
    while (pagination.firstChild) {
      pagination.removeChild(pagination.firstChild);
    }
  }

function createPaginationLinks(tableId, totalPages, currentPage, buttonsPerGroup) {
    clearPagination(tableId);
    // Get the pagination container
    var pagination = document.getElementById(tableId + "-pagination");
    // Clear the existing links
    pagination.innerHTML = "";
    // Add the "previous" button
    var prevButton = document.createElement("li");
    prevButton.classList.add("page-item");
    if (currentPage === 1) {
      prevButton.classList.add("disabled");
    }
    var prevLink = document.createElement("a");
    prevLink.classList.add("page-link");
    prevLink.href = "?page=" + (currentPage - 1);
    prevLink.innerHTML = "<";
    prevButton.appendChild(prevLink);
    pagination.appendChild(prevButton);
    // Calculate the range of buttons to show
    var start = currentPage - Math.floor(buttonsPerGroup / 2);
    var end = currentPage + Math.floor(buttonsPerGroup / 2);
    if (start < 1) {
      start = 1;
      end = Math.min(totalPages, buttonsPerGroup);
    }
    if (end > totalPages) {
      end = totalPages;
      start = Math.max(1, totalPages - buttonsPerGroup + 1);
    }
    // Add the page buttons
    for (var i = start; i <= end; i++) {
      var button = document.createElement("li");
      button.classList.add("page-item");
      if (i === currentPage) {
        button.classList.add("active");
      }
      var link = document.createElement("a");
      link.classList.add("page-link");
      link.href = "?page=" + i;
      link.innerHTML = i;
      button.appendChild(link);
      pagination.appendChild(button);
    }
    // Add the "next" button
    var nextButton = document.createElement("li");
    nextButton.classList.add("page-item");
    if (currentPage === totalPages) {
        nextButton.classList.add("disabled");
    }
    var nextLink = document.createElement("a");
    nextLink.classList.add("page-link");
    nextLink.href = "?page=" + (currentPage + 1);
    nextLink.innerHTML = ">";
    nextButton.appendChild(nextLink);
    pagination.appendChild(nextButton);
}

function getUrlParameter(name) {
    var searchString = window.location.search.substring(1);
    var parameters = searchString.split("&");
    for (var i = 0; i < parameters.length; i++) {
        var parameter = parameters[i].split("=");
        if (parameter[0] === name) {
            return parameter[1];
        }
    }
    return null;
}


function fillTable(data, tableId, itemsPerPage) {
    // Get the table element
    var table = document.getElementById(tableId);
    // Clear the existing rows
    for(var i = 1;i<table.rows.length;){
        table.deleteRow(i);
    }
    // Divide the data into pages
    var pages = paginate(data, itemsPerPage);
    // Get the current page number from the URL or set it to 1
    var currentPage = parseInt(getUrlParameter("page")) || 1;
    // Get the current page of data
    var pageData = pages[currentPage - 1];
    // Loop through the page data and add a new row for each object
    pageData.forEach(function(person) {
        var row = table.insertRow();
        var nameCell = row.insertCell();
        var link = document.createElement("a");
        link.href = "../person?person_id=" + person.id;
        nameCell.appendChild(link);
        var descCell = row.insertCell();
        var rolesCell = row.insertCell();
        var appearancesCell = row.insertCell();
        var idCell = row.insertCell();

        //Name
        let name = [person['name_first'] , " " , person['name_nickname'], " " , person['name_last'], " ", person['name_suffix']].join('')
        link.innerHTML = name;

        //Description
        if('desc_brief' in person) {
            descCell.innerHTML = person.desc_brief;
        }
  
        if('role' in person) {
            let roles = person['role']
            let proper_roles = []
            for(role in roles){
                proper_roles[role] = roles[role].charAt(0).toUpperCase() + roles[role].slice(1);
            }
            let role_string = proper_roles.join(', ')
            rolesCell.innerHTML = role_string;
        }

        if('appearances' in person) {
            appearancesCell.innerHTML = person.appearances.length;
        } else {
            appearancesCell.innerHTML = 0;
        }

        idCell.innerHTML = person.id;
    });

    // Call the function to create the pagination links
    createPaginationLinks(tableId, pages.length, currentPage, 5);
}



var limit = 10

fetch('ingest_api/people')
.then((response) => response.json())
.then((data) => fillTable(data, 'dataTable', limit));

document.getElementById("personSearch").addEventListener("submit", function(event){
    event.preventDefault();
    let formData = new FormData(this);
    let searchString = document.getElementById("searchInput").value;
    fetch('http://172.25.2.99:8001/people?search_text=' + searchString)
    .then((response) => response.json())
    .then((data) => fillTable(data, 'dataTable', limit));
});