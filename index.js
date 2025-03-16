const socket = io("http://localhost:8000");

socket.on("connect", () => {
    console.log("Connected to WebSocket server");
});

function sendMessage() {
    const userMessage = document.getElementById("userInput").value;

    socket.emit("message", { message: userMessage, history: [] });

    socket.on("response", (data) => {
        console.log("Bot:", data.message);
        document.getElementById("chat").innerHTML += `<p>Bot: ${data.message}</p>`;
    });
}
