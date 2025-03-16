from function import (
    handle_cancellation, handle_reschedule, handle_inquiry, 
    handle_flight_booking, understand_request, 
    Travelchat, collect_details
)

import socket
import os
import socketio
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END


load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is missing from environment variables.")


def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        raise ConnectionError("No internet connection available.")

# Initialize LLM
llm = ChatOpenAI(
    model="llama3-8b-8192",
    openai_api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)


required_fields = {
    "flight_booking": ["departure", "destination", "date", "what-time", "preferred_airline", "payment_method"],
    "reschedule": ["booking_id", "new_date", "what-time"],
    "cancellation": ["booking_id"],
    "inquiry": ["booking_id"],
}


def process_request(state: Travelchat):
    last_user_message = state["messages"][-1]["content"]
    intent, details, messages = state["intent"], state["details"], state["messages"]

    response_map = {
        "flight_booking": handle_flight_booking,
        "reschedule": handle_reschedule,
        "cancellation": handle_cancellation,
        "inquiry": handle_inquiry,
    }

    try:
        is_connected()
        if intent in response_map:
            state = response_map[intent](state)
            response_text = state["response"]
        else:
            response = llm.invoke(last_user_message)
            response_text = response.content.strip() if response else "I'm not sure how to help with that."
            state = {"messages": messages + [{"role": "assistant", "content": response_text}], "intent": intent, "details": details}
    except ConnectionError:
        response_text = "No internet connection. Please check your network."
        state = {"messages": messages + [{"role": "assistant", "content": response_text}], "intent": intent, "details": details}
    except Exception as e:
        response_text = f"Error: {str(e)}"
        state = {"messages": messages + [{"role": "assistant", "content": response_text}], "intent": intent, "details": details}

    return state


def create_chatbot():
    workflow = StateGraph(Travelchat)

    workflow.add_node("understand_request", understand_request)
    workflow.add_node("collect_details", collect_details)
    workflow.add_node("process_request", process_request)
    
    workflow.set_entry_point("understand_request")

    workflow.add_conditional_edges(
        "understand_request",
        lambda state: "collect_details" if state.get("intent") in required_fields else "process_request"
    )
    workflow.add_conditional_edges(
        "collect_details",
        lambda state: "process_request" if all(field in state["details"] for field in required_fields.get(state["intent"], [])) else "collect_details"
    )
    workflow.add_conditional_edges("process_request", lambda state: END)

    workflow.set_finish_point(END)
    
    return workflow.compile()

chatbot = create_chatbot()


app = FastAPI()

# Socket.IO Server
class SocketServer:
    def __init__(self, app, chatbot):
        self.graph = chatbot
        self.app = app
        self.sio = socketio.AsyncServer(cors_allowed_origins='*', async_mode='asgi')
        self.socket_app = socketio.ASGIApp(self.sio)
        self.app.mount("/", self.socket_app)
        self.register_events()

    def register_events(self):
        @self.sio.on("connect")
        async def connect(sid, _env):
            print(f"Client connected: {sid}")
            await self.sio.emit("server_message", "Welcome to the Travel Chatbot!")

        @self.sio.on("message")
        async def handle_message(sid, data):
            user_input = data.get("input", "")
            thread_id = data.get("thread_id", "default_session")
            state = {"messages": [{"role": "user", "content": user_input}], "intent": None, "details": {}}

            print(f"User ({sid}): {user_input}")

            # Process request through LangGraph
            for event in self.graph.stream(state, stream_mode="values"):
                if event == END:
                    break

            await self.sio.emit("bot_response", {"response": "Request processed."})

# Start Socket.IO server
socket_server = SocketServer(app, chatbot)

# Run the FastAPI server
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3500, reload=True)
