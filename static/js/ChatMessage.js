export function ChatMessage({ sender, text }) {
    return `
        <div class="message ${sender}">
            <div class="message-content">
                ${text}
            </div>
        </div>
    `;
}
