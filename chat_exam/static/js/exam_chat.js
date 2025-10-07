// === Exam chat logic ===
window.addEventListener('DOMContentLoaded', () => {

    let questions = [];
    let index = 0;

    const chatBox = document.getElementById('chat-box');
    const input = document.getElementById('answer');
    const sendBtn = document.getElementById('send-btn');

    function addBubble(text, type) {
        const bubble = document.createElement('div');
        bubble.className = 'bubble ' + type;
        bubble.textContent = text;
        chatBox.appendChild(bubble);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function nextQuestion() {
        if (index < questions.length) {
            addBubble(questions[index], 'question');
        } else {
            addBubble('You have completed the exam ✅', 'system');
            input.disabled = true;
            sendBtn.disabled = true;
        }
    }

    function sendAnswer() {
        const text = input.value.trim();
        if (!text) return;
        addBubble(text, 'answer');
        input.value = '';
        index++;
        setTimeout(nextQuestion, 500);
    }

    window.initExamChat = function(qs) {
        questions = qs;
        nextQuestion();
        sendBtn.addEventListener('click', sendAnswer);
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendAnswer();
        });
    };
});
