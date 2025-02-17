import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
import { toast } from "./base.js";

const messagesElement = document.getElementById("messages");
const formElement = document.getElementById("form");

const messages = [
  {
    role: "bot",
    content: "Hello! How can I help you today?",
  },
];

function createMessageElement(name, content) {
  const card = document.createElement("div");
  card.classList.add("container");
  card.classList.add("card");

  const cardBody = document.createElement("div");
  cardBody.classList.add("card-body");

  const cardTitle = document.createElement("h5");
  cardTitle.classList.add("card-title");
  cardTitle.innerHTML = name;

  const cardText = document.createElement("p");
  cardText.classList.add("card-text");
  cardText.innerHTML = content;

  cardBody.appendChild(cardTitle);
  cardBody.appendChild(cardText);
  card.appendChild(cardBody);

  return card;
}

function renderMessages() {
  // Clear chat
  messagesElement.innerHTML = "";

  // Render messages
  messages.forEach(({ role, content }) => {
    const name = role === "bot" ? "Eco Bot" : "You";
    const messageElement = createMessageElement(name, marked.parse(content));
    messagesElement.appendChild(messageElement);
  });

  // Scroll to bottom of chat
  messagesElement.scrollTop = messagesElement.scrollHeight;
}

function sendMessage(event) {
  // Prevent default behavior; refresh page
  event.preventDefault();

  // Get form data
  const data = new FormData(event.target);
  const entries = Object.fromEntries(data.entries());
  const { content } = entries;

  if (!content) {
    toast("Please enter a message!", "danger");
    return;
  }

  // Clear fields
  event.target.reset();

  // Add user message to chat
  messages.push({ role: "user", content });
  renderMessages();

  // Send data to server
  fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      prompt: content,
      history: messages.map((message) => {
        return { role: message.role, content: message.content };
      }),
    }),
  })
    .then((res) => {
      // Handle errors
      if (!res.ok) return Error(res.statusText);

      // Parse response
      return res.json();
    })
    .then((data) => {
      // Parse data
      const { response } = data;

      // Add bot response to chat
      messages.push({ role: "bot", content: response });
    })
    .catch((error) => {
      console.error(error);
      toast("An error had occurred! Please check the console for more information.", "danger");
    })
    .finally(() => {
      renderMessages();
    });
}

formElement.addEventListener("submit", sendMessage);

renderMessages();