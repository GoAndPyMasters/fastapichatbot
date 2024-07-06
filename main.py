import os
import google.generativeai as genai
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
from dotenv import load_dotenv


load_dotenv()


API_KEY = os.getenv("API_KEY")

app = FastAPI(
    title="AI Chat API",
    docs_url='/',
    description="This API allows you to chat with an AI model using WebSocket connections.",
    version="1.0.0"
)

# Define CORS settings if necessary
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity; adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/chat", tags=["Chat"])

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@router.get("/")
async def get():

    """
    WebSocket endpoint for handling chat messages.
    
    This WebSocket endpoint allows clients to send messages to the AI model
    and receive streamed responses.

    To use this endpoint, establish a WebSocket connection to `/ws`.

    - Send a message to the WebSocket.
    - Receive a response from the AI model.
    - If the message "exit" is sent, the chat session will end.
    """    

    return HTMLResponse("""
    <html>
        <head>
            <title>Chat with AI</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f9;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                #chat-container {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    width: 400px;
                    max-width: 100%;
                }
                h1 {
                    text-align: center;
                    color: #333;
                }
                form {
                    display: flex;
                    margin-top: 20px;
                }
                input[type="text"] {
                    flex: 1;
                    padding: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    margin-right: 10px;
                }
                button {
                    padding: 10px 20px;
                    border: none;
                    background-color: #007BFF;
                    color: white;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #0056b3;
                }
                ul {
                    list-style: none;
                    padding: 0;
                    max-height: 300px;
                    overflow-y: auto;
                }
                li {
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }
                .user-message {
                    text-align: right;
                    color: #007BFF;
                }
                .ai-message {
                    text-align: left;
                    color: #333;
                }
            </style>
        </head>
        <body>
            <div id="chat-container">
                <h1>Chat with AI</h1>
                <ul id="messages"></ul>
                <form action="" onsubmit="sendMessage(event)">
                    <input type="text" id="messageText" autocomplete="off"/>
                    <button>Send</button>
                </form>
            </div>
            <script>
                var ws = new WebSocket("ws://0.0.0.0:8000/chat/ws");
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    var content = document.createTextNode(event.data);
                    message.appendChild(content);
                    if (event.data.startsWith("AI:")) {
                        message.className = "ai-message";
                    } else {
                        message.className = "user-message";
                    }
                    messages.appendChild(message);
                };
                function sendMessage(event) {
                    var input = document.getElementById("messageText");
                    var userMessage = "You: " + input.value;
                    ws.send(userMessage);
                    // Display user message immediately
                    var messages = document.getElementById('messages');
                    var message = document.createElement('li');
                    var content = document.createTextNode(userMessage);
                    message.appendChild(content);
                    message.className = "user-message";
                    messages.appendChild(message);
                    input.value = '';
                    event.preventDefault();
                }
            </script>
        </body>
    </html>
    """)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for handling chat messages.
    
    This WebSocket endpoint allows clients to send messages to the AI model
    and receive streamed responses.

    To use this endpoint, establish a WebSocket connection to `/ws`.

    - Send a message to the WebSocket.
    - Receive a response from the AI model.
    - If the message "exit" is sent, the chat session will end.
    """
    await websocket.accept()
    chat = model.start_chat(history=[])
    try:
        while True:
            data = await websocket.receive_text()
            if data.lower().startswith("you: "):
                user_message = data[5:]
                if user_message.lower() == "exit":
                    await websocket.send_text("AI: Ending chat session.")
                    break
                response = chat.send_message(user_message, stream=True)
                full_response = ""
                for chunk in response:
                    full_response += chunk.text
                await websocket.send_text("AI: " + full_response)
            else:
                await websocket.send_text("AI: Please start your message with 'You: '")
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        await websocket.close()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
# uvicorn main:app --host 0.0.0.0 --port 8000
