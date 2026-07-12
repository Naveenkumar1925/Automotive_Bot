// script.js — sends chat messages to the Python API and renders the conversation.

const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const sendBtn = document.getElementById("send-btn");
const messages = document.getElementById("messages");

// On load, fetch any existing conversation history from the server.
window.addEventListener("DOMContentLoaded", loadHistory);

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  // Show the user's message immediately, then clear and lock the input.
  addBubble({ sender: "user", text, time: timeNow() });
  input.value = "";
  setSending(true);

  const typing = showTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const data = await response.json();
    typing.remove();

    if (response.ok) {
      addBubble(data.reply); // { sender: "bot", text, time }
    } else {
      addBubble({ sender: "bot", text: `Error: ${data.error}`, time: timeNow() });
    }
  } catch (err) {
    typing.remove();
    addBubble({
      sender: "bot",
      text: "Could not reach the server. Is it running?",
      time: timeNow(),
    });
  } finally {
    setSending(false);
    input.focus();
  }
});

async function loadHistory() {
  try {
    const response = await fetch("/api/history");
    const data = await response.json();
    data.history.forEach(addBubble);
  } catch (err) {
    // No history available yet — that's fine.
  }
}

function addBubble({ sender, text, time }) {
  const row = document.createElement("div");
  row.className = `row ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = sender === "user" ? "You" : "AI";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  const stamp = document.createElement("span");
  stamp.className = "time";
  stamp.textContent = time;
  bubble.appendChild(stamp);

  row.appendChild(avatar);
  row.appendChild(bubble);
  messages.appendChild(row);
  scrollToBottom();
  return row;
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "row bot typing";
  row.innerHTML =
    '<div class="avatar">AI</div><div class="bubble"><span></span><span></span><span></span></div>';
  messages.appendChild(row);
  scrollToBottom();
  return row;
}

function setSending(isSending) {
  sendBtn.disabled = isSending;
  input.disabled = isSending;
}

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function timeNow() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}
