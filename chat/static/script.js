document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".chat-form");
    const messages = document.querySelector(".messages");

    if (form) {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const input = form.querySelector("input");
            const text = input.value.trim();

            if (text) {
                const userMsg = document.createElement("p");
                userMsg.textContent = "You: " + text;
                messages.appendChild(userMsg);

                // Fake bot response
                const botMsg = document.createElement("p");
                botMsg.textContent = "Bot: I received -> " + text;
                botMsg.classList.add("bot-msg");
                messages.appendChild(botMsg);

                messages.scrollTop = messages.scrollHeight;
                input.value = "";
            }
        });
    }
});
