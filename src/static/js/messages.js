// messages.js
const socket = io({
	transports: ["polling"],
});

// Store current chat state
let currentRecipientId = null;
let currentSenderId = null;

function displayMessage(message) {
	const messageSpace = document.querySelector(".message-space");
	const messageBlock = document.createElement("div");
	messageBlock.className = `message-block ${message.sender_id === currentSenderId ? "you" : "other-person"}`;
	messageBlock.id = message.id;

if (message.sender_id == currentSenderId && message.is_visible) {
    messageBlock.innerHTML = `
    <form action="/community/messages/${message.receiver_id}/${message.id}" method="POST">
      <div class="message card rounded-3">
        <div class="card-body">
          <p class="card-text">${message.message}</p>
          <button type="submit" class="btn btn-danger btn-sm float-end">Delete</button>
        </div>
      </div>
    </form>
    `;
    console.log(`test: logged in user = sender, sender id = ${message.sender_id}, current sender id = ${currentSenderId}`);
  } else if (message.receiver_id == currentSenderId && message.is_visible){
    messageBlock.innerHTML = `
    <form action="/community/messages/${message.receiver_id}/${message.id}" method="POST">
      <div class="message card rounded-3">
        <div class="card-body">
          <p class="card-text">${message.message}</p>
        </div>
      </div>
    </form>
    `;
    console.log(`test: logged in user = receiver, sender id = ${message.sender_id}, current sender id = ${currentSenderId}`);
  }
	messageSpace.appendChild(messageBlock);
	messageSpace.scrollTop = messageSpace.scrollHeight;
}


document.addEventListener("DOMContentLoaded", function () {
	currentSenderId = document.querySelector("#sender-id").value;
	currentRecipientId = window.location.pathname.split("/")[3];
  console.log(currentRecipientId)

	fetch(`/api/messages?sender_id=${currentSenderId}&receiver_id=${currentRecipientId}`)
		.then((response) => {
			return response.json();
		})
		.then((messages) => {
			messages.forEach((message) => displayMessage(message));
		});

	// Socket event listeners
	socket.on("connect", () => {
		console.log("Connected to Socket.IO server");

		if(currentRecipientId) {
			socket.emit("join",  { receiver_id: currentRecipientId });
		}
	});

	socket.on("receive_message", (messages) => {
		const messageSpace = document.querySelector(".message-space");
		messageSpace.innerHTML = "";
		fetch(`/api/messages?sender_id=${currentSenderId}&receiver_id=${currentRecipientId}`)
			.then((response) => {
				return response.json();
			})
			.then((messages) => {
				messages.forEach((message) => displayMessage(message));
			});
	});
});


function editMessage(form, id) {
	const message = document.querySelector(`#${id} .message p`).textContent;
	prompt("Enter the new content of your message.", message);
}

function join_room(receiver_id) {
	socket.emit("join", {receiver_id: receiver_id});

	messageSpace.innerHTML = "";
	fetch(`/api/messages?sender_id=${currentSenderId}&receiver_id=${receiver_id}`)
	.then((response) => response.json())
	.then((messages) => {
		const messageSpace = document.querySelector(".message-space");
		messageSpace.innerHTML = "";  // Clear any old messages
		messages.forEach((message) => displayMessage(message));  // Display new messages

		// Update the current recipient to the new one
		currentRecipientId = receiver_id;
	});

}

function sendMessage() {
	console.log("running sendMessage()");
	const inputElement = document.querySelector("input#message");
	const content = inputElement.value;
	inputElement.value = "";
	console.log(content)
    socket.emit("send_message", {
        sender_id: currentSenderId,
        receiver_id: currentRecipientId,
        message: content
    });

};

socket.on("receive_message", (message) => {
    // Check if this message belongs to current chat
    if (message.sender_id === currentRecipientId ||
        (message.sender_id === currentSenderId && message.receiver_id === currentRecipientId)) {
        displayMessage(message);
    }
});

socket.on("message_deleted", (data) => {
  location.reload();
});

document.addEventListener("DOMContentLoaded", function () {
  const inputElement = document.querySelector("input#message");

  inputElement.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      event.preventDefault(); // Prevent the default form submission
      sendMessage(); // Trigger the sendMessage function
    }
  });
});


socket.on("message_restored", () =>  {
  location.reload();
})
