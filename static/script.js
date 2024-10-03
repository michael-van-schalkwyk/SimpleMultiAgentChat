// static/script.js
const socket = new WebSocket('ws://' + window.location.host + '/ws');
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');

socket.onmessage = function(event) {
    const message = JSON.parse(event.data);
    displayMessage(message);
};

function sendMessage() {
    const content = userInput.value.trim();
    if (content) {
        const message = {
            role: 'user',
            content: content
        };
        socket.send(JSON.stringify(message));
        displayMessage(message);
        userInput.value = '';
    }
}

function displayMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message', message.role);
    messageElement.textContent = `${message.role}: ${message.content}`;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

userInput.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});