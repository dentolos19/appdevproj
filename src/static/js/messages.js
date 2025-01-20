// messages.js
const socket = io();

// Store current chat state
let currentRecipientId = null;
let currentSenderId = null;

function displayMessage(message) {
	const messageSpace = document.querySelector(".message-space");
	const messageBlock = document.createElement("div");
	messageBlock.className = `message-block ${message.sender_id === currentSenderId ? "you" : "other-person"}`;
	messageBlock.id = message.id;

	if (message.sender_id == currentSenderId) {
		
		messageBlock.innerHTML = `
		<form action="/community/messages/${message.receiver_id}/${message.id}" method="POST">
			<div class="message">
				<p>${message.message}</p>
				<span class="timestamp">Read status: ${message.is_read ? "Read" : "Unread"}</span>
				<button type="submit">Delete</button> 
			</div>
		</form>
		`;
		console.log(`test: logged in user = sender, sender id = ${message.sender_id}, current sender id = ${currentSenderId}`);
	} else {
		
		messageBlock.innerHTML = `
		<form action="/community/messages/${message.receiver_id}/${message.id}" method="POST">
			<div class="message">
				<p>${message.message}</p>
				<span class="timestamp">Read status: ${message.is_read ? "Read" : "Unread"}</span>
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
	currentRecipientId = document.querySelector("#receiver-id").value;

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
		// TODO: Fix socket updates
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