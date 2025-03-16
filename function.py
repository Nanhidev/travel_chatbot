from db import execute_db_query ,generate_id , fetch_booking_details 
from intent import detect_intent


from typing import TypedDict , Optional


required_fields = {
    "flight_booking": ["departure", "destination", "date", "what-time", "preferred_airline", "payment_method"],
    "reschedule": ["booking_id", "new_date", "what-time"],
    "cancellation": ["booking_id"],
    "inquiry": ["booking_id"]
}


class Travelchat(TypedDict):
    input: str 
    intent: Optional[str]
    booking_details: Optional[dict]  
    user_feedback: Optional[str]



import dateparser

def understand_request(state: Travelchat):
    user_input = input("User: ").strip()
    conversation_history = state.get("messages", [])
    intent = detect_intent(user_input, conversation_history)
    new_messages = conversation_history + [{"role": "user", "content": user_input}]
    return {"messages": new_messages, "intent": intent, "details": state.get("details", {})}


def collect_details(state: Travelchat):
    intent = state["intent"]
    details = state["details"]
    missing_fields = [field for field in required_fields.get(intent, []) if field not in details]
    
    for field in missing_fields:
        value = input(f"Enter {field.replace('_', ' ')}: ").strip()


        if field == "date":  
            parsed_date = dateparser.parse(value)
            details[field] = parsed_date.strftime("%Y-%m-%d") if parsed_date else value
        else:
            details[field] = value  


    return {"messages": state["messages"], "intent": intent, "details": details}


def collect_group_details():
    passengers = []
    num_passengers = int(input("how many number of passengers: "))
    
    for i in range(num_passengers):
        name = input(f"Enter name for passenger {i + 1}: ").strip()
        age = input(f"Enter age for passenger {i + 1}: ").strip()
        passengers.append((name, age))
    
    return passengers


def handle_flight_booking(state: Travelchat):
    details = state["details"]
    details["booking_id"] = generate_id()

    passengers = collect_group_details() 

    query = '''
        INSERT INTO bookings (booking_id, departure, destination, date, time, preferred_airline, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''

    rows_affected = execute_db_query(query, (
        details["booking_id"], details["departure"], details["destination"], details["date"], 
        details["what-time"], details["preferred_airline"], details["payment_method"]
    ), fetch=False)

    if rows_affected is None:
        return {"messages": state["messages"], "intent": "flight_booking", "details": details, "response": "Database insertion failed."}

    for name, age in passengers:
        execute_db_query('INSERT INTO passengers (booking_id, name, age) VALUES (?, ?, ?)', 
                         (details["booking_id"], name, age), fetch=False)

    response = (
        f"Your flight from {details['departure']} to {details['destination']} "
        f"on {details['date']} at {details['what-time']} is booked.\n"
        f"Passengers: " + ", ".join([f"{p[0]} (Age: {p[1]})" for p in passengers])
    )

    return {"messages": state["messages"], "intent": "flight_booking", "details": details, "response": response}





def handle_inquiry(state):
    user_messages = state.get("messages", [])

    
    details = state.get("details", {})

  
    booking_id = details.get("booking_id", "").strip()

    if not booking_id:
        return {
            "messages": user_messages + ["Enter booking id:"],
            "intent": "inquiry",
            "response": "Enter booking id:" 
        }

    booking_id = booking_id.split("-")[0]

    print(f"Extracted Booking ID: {booking_id}")  
    
    booking = fetch_booking_details(booking_id)

    if not booking:
        print(f" No booking found for ID: {booking_id}")  
        return {
            "messages": user_messages,
            "intent": "inquiry",
            "response": f"No booking found with ID {booking_id}. Please check and try again."
        }


    booking_id, departure, destination, date, what_time, booking_date, payment_method = booking

    response = f"""
**Booking Details:**
- **Booking ID:** {booking_id}
- **Departure:** {departure}
- **Destination:** {destination}
- **Date:** {date}
- **Time:** {what_time}
- **Booking Date:** {booking_date}
- **Payment Method:** {payment_method}
    """.strip()

    return {
        "messages": user_messages,
        "intent": "inquiry",
        "response": response
    }



def handle_reschedule(state: Travelchat):
    details = state["details"]
    execute_db_query('UPDATE bookings SET date = ?, time = ? WHERE booking_id = ?',
                     (details.get('new_date'), details.get('what-time'), details.get('booking_id')))
    response = (
        f"Your booking has been rescheduled to {details.get('new_date', 'unknown')} at {details.get('what-time', 'unknown time')}."
    )
    return {"messages": state["messages"], "intent": "reschedule", "details": details, "response": response}



def handle_cancellation(state: Travelchat):
    details = state["details"]
    booking_id = details.get('booking_id')

    query = 'DELETE FROM bookings WHERE booking_id = ?'
    rows_affected = execute_db_query(query, (booking_id,), fetch=False)

    response = f"Your booking (ID: {booking_id}) has been canceled." if rows_affected else f"Booking ID {booking_id} not found."

    return {"messages": state["messages"], "intent": "cancellation", "details": details, "response": response}








