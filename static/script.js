document.getElementById("send-btn").addEventListener("click", async () => {
    const userInput = document.getElementById("user-input").value;
    if (!userInput) return;

    // Add user message to chat box
    const chatBox = document.getElementById("chat-box");
    const userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    // Clear input
    document.getElementById("user-input").value = "";

    // Send user input to backend
    const response = await fetch("/get_advice", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userInput }),
    });

    const data = await response.json();

    // Add AI response to chat box
    const aiMessage = document.createElement("div");
    aiMessage.className = "ai-message";
    aiMessage.textContent = data.response;
    chatBox.appendChild(aiMessage);

    // Scroll to bottom of chat box
    chatBox.scrollTop = chatBox.scrollHeight;

    // Play the voice reply
    const audioPlayer = document.getElementById("audio-player");
    audioPlayer.src = data.audio_file;
    audioPlayer.play();
}); 