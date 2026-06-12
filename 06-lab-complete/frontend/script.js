const chatForm = document.getElementById('chat-form');
const questionInput = document.getElementById('question-input');
const chatHistory = document.getElementById('chat-history');
const apiKeyInput = document.getElementById('api-key');
const userIdInput = document.getElementById('user-id');

function addMessage(text, type) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
    msgDiv.textContent = text;
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-msg typing';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    typingDiv.id = 'typing-indicator';
    chatHistory.appendChild(typingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    const apiKey = apiKeyInput.value.trim();
    const userId = userIdInput.value.trim();

    // Add user message to UI
    addMessage(question, 'user-msg');
    questionInput.value = '';
    
    // Show typing animation
    showTyping();

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey
            },
            body: JSON.stringify({
                user_id: userId,
                question: question
            })
        });

        const data = await response.json();
        removeTyping();

        if (response.ok) {
            addMessage(data.response, 'bot-msg');
        } else {
            // Handle HTTP errors
            let errorMsg = data.detail || 'An error occurred';
            if (response.status === 401) errorMsg = '🔒 Unauthorized: Invalid API Key';
            if (response.status === 429) errorMsg = '⏳ Rate limit exceeded (10 req/min). Please wait.';
            if (response.status === 402) errorMsg = '💰 Budget exceeded for this month.';
            
            addMessage(errorMsg, 'error-msg');
        }
    } catch (error) {
        removeTyping();
        addMessage('Network error. Could not connect to the server.', 'error-msg');
    }
});
