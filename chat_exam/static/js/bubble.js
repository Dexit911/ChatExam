function toggleRenameBubble(event, examId, currentTitle) {
    event.stopPropagation(); // prevent bubble from closing immediately

    // Close all open bubbles first
    document.querySelectorAll('.rename-bubble').forEach(b => b.style.display = 'none');

    const bubble = document.getElementById(`rename-bubble-${examId}`);
    const input = bubble.querySelector('input');

    // Toggle current bubble
    bubble.style.display = (bubble.style.display === 'block') ? 'none' : 'block';
    input.value = currentTitle;

    // Focus input when shown
    if (bubble.style.display === 'block') {
        input.focus();
    }
}

// Close on outside click
document.addEventListener('click', (e) => {
    if (!e.target.closest('.rename-bubble') && !e.target.closest('.icon-btn')) {
        document.querySelectorAll('.rename-bubble').forEach(b => b.style.display = 'none');}