console.log('starting...')

const instModalElement = document.getElementById('instance_modal');
const instModal = new bootstrap.Modal(instModalElement);

console.log("running...")

document.getElementById("new_instance").addEventListener('click', openInstModal);
console.log('listening...')

  // Function to open the song modal
function openInstModal() {
    // Show the song modal
    instModal.show();
    console.log('opening...')
}
