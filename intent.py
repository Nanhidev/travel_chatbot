from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.environ["GROQ_API_KEY"]

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model= "llama3-8b-8192",
    openai_api_key = api_key,
    base_url="https://api.groq.com/openai/v1"
)



def detect_intent(user_input: str, conversation_history: list):
    user_input = user_input.lower().strip()

    
    inquiry_keywords = ["fetch booking details", "get my booking", "retrieve booking", "booking inquiry"]

    
    if any(keyword in user_input for keyword in inquiry_keywords):
        return "inquiry"

    prompt = f"""
    You are a smart travel assistant. Your job is to understand the user's intent.

    ### Conversation History:
    {conversation_history}

    ### User Input:
    {user_input}

    Classify the intent:
    - "flight_booking" → If user wants to book a flight
    - "reschedule" → If user wants to change an existing booking
    - "cancellation" → If user wants to cancel a booking
    - "inquiry" → If user is asking for booking details (Booking ID ,required)
    - "general_inquiry" → If user asks general questions
    **Return only the intent as a single word.**
    """

    try:
        response =llm.invoke(prompt).content.strip().lower()
        valid_intents = {"flight_booking", "reschedule", "cancellation", "general_inquiry", "inquiry"}
        
        return response if response in valid_intents else "general_inquiry"

    except Exception as e:
        print(e)
        return "general_inquiry"


