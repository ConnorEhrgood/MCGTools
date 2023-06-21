console.log('starting...')

const instModalElement = document.getElementById('instance_modal');
const instModal = new bootstrap.Modal(instModalElement);

const importFields = document.getElementById('import_fields')
const fileSelect = document.getElementById('file_select')
const fileHeader = document.getElementById('file_header')
const fileSpinner = document.getElementById('file_select_spinner')
const locationHeader = document.getElementById('location_header')
const instLocation = document.getElementById('instance_location')

fileSelect.style.display = 'none'
fileHeader.style.display = 'none'
fileSpinner.style.display = 'none'

let newInstances = [];



function loadStagedFiles(items) {
  const fileSelect = document.getElementById('file_select');

  // Clear any existing options
  fileSelect.innerHTML = '';

  // Iterate over the items and create option elements
  items.forEach(item => {
    const option = document.createElement('option');
    option.value = item;
    option.textContent = item;
    fileSelect.appendChild(option);
  });

  fileSelect.style.display = 'block'
  fileHeader.style.display = 'block'

  fileSpinner.style.display = 'none'

};


function getStagedFiles() {

  fetch('ingest_api/staged_files')
  .then((response) => response.json())
  .then((data) => loadStagedFiles(data));

}



document.getElementById("instance_medium").addEventListener("change", function() {

  // Show the relevant field div based on the selected tag type
  const selectedMedium = this.value;
  if (selectedMedium === "0") {
    importFields.style.display = "block";
  } else {
    importFields.style.display = 'none'
  }

});

document.getElementById("import_type").addEventListener("change", function() {

  // Show the relevant field div based on the selected tag type
  const selectedMedium = this.value;
  if (selectedMedium === "2") {

    fileSpinner.style.display = 'block'

    instLocation.style.display = 'none'
    locationHeader.style.display = 'none'

    getStagedFiles()

  } else {
    fileSelect.style.display = 'none'
    fileHeader.style.display = 'none'

    instLocation.style.display = 'block'
    locationHeader.style.display = 'block'
  }

});

console.log("running...")

document.getElementById("new_instance").addEventListener('click', openInstModal);
console.log('listening...')

  // Function to open the song modal
function openInstModal() {
    // Show the song modal
    instModal.show();
    console.log('opening...')
}



function captureFormSubmission() {
  console.log('instance added...');
  var instanceType = document.getElementById('instance_type').value;
  var instanceMedium = document.getElementById('instance_medium').value;
  var instanceGeneration = document.getElementById('instance_generation').value;
  var importType = document.getElementById('import_type').value;
  var instanceLocation = document.getElementById('instance_location').value;
  var fileSelect = document.getElementById('file_select');
  var selectedFiles = [];

  for (var i = 0; i < fileSelect.options.length; i++) {
    if (fileSelect.options[i].selected) {
      selectedFiles.push(fileSelect.options[i].text);
    }
  }

  var newInstance = {
    instanceType: instanceType,
    instanceMedium: instanceMedium,
    instanceGeneration: instanceGeneration,
    importType: importType,
    instanceLocation: instanceLocation,
    selectedFiles: selectedFiles
  };

  newInstances.push(newInstance); // Assuming `newInstances` is already defined

  console.log(newInstance); // Optional: Log the new instance object
}



document.getElementById('instance_form').addEventListener('submit', function(event) {
  event.preventDefault(); // Prevent the form from being submitted normally
  captureFormSubmission();
});