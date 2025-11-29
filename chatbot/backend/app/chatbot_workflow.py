from typing import TypedDict

from app.tools.appointment_tool import AppointmentTool
from app.tools.data_tool import DataTool
from app.tools.inference_tool import InferenceTool
from langgraph.graph import END, START, StateGraph


# Define state
class ChatState(TypedDict):
    query: str
    intent: str
    confidence: float
    response: str
    appointment_action: str
    datetime: str
    conversation_state: dict


# Initialize tools
tool = InferenceTool()
appt_tool = AppointmentTool()
rag_tool = DataTool()


# Define nodes
def intent_analysis(state: ChatState):
    query_lower = state["query"].lower()
    
    # IMPORTANT: Check for cancel/reschedule keywords FIRST before ML model
    # This prevents false matches (e.g., "I need to reschedule" matching "I need" as booking)
    cancel_keywords = [
        "cancel", "remove", "delete", "cancel my", "cancel the",
        "cancelled", "canceling", "cancelling", "want to cancel",
        "need to cancel", "i want to cancel", "i need to cancel",
        "cancellation"
    ]
    reschedule_keywords = [
        "reschedule", "change", "modify", "move", "shift", "postpone",
        "rescheduling", "changing", "modifying", "moving", "shifting",
        "need to reschedule", "want to reschedule", "i need to reschedule",
        "i want to reschedule"
    ]
    
    # Check cancel/reschedule FIRST - these should override ML model if present
    has_cancel = any(word in query_lower for word in cancel_keywords)
    has_reschedule = any(word in query_lower for word in reschedule_keywords)
    
    # Try to use the ML model, fallback to keyword-based detection if it fails
    ml_intent_set = False
    try:
        result = tool.predict_and_respond(state["query"])
        state["intent"] = result["intent"]
        state["confidence"] = result["confidence"]
        state["response"] = result["response"]
        ml_intent_set = True
    except Exception as e:
        # Fallback to keyword-based intent detection
        state["confidence"] = 0.7  # Default confidence for keyword-based
        state["intent"] = "greeting"  # Default intent
        state["response"] = "Hello! How can I help with your booking?"

    # Override ML model intent if cancel/reschedule keywords are present
    # This ensures "I need to reschedule" is caught even if ML model says "book_service"
    if has_cancel:
        state["intent"] = "cancel_booking"
        state["response"] = "Got it. Confirm if you want to cancel."
        state["confidence"] = 0.9
    elif has_reschedule:
        state["intent"] = "reschedule_booking"
        state["response"] = "Sure, let's reschedule. Provide the new date and time."
        state["confidence"] = 0.9

    # Keyword-based intent detection (used as fallback or enhancement)
    # Expanded booking keywords to catch many variations
    booking_keywords = [
        "book", "schedule", "appointment", "reserve", "reservation",
        "set up", "setup", "make", "create", "arrange", "organize",
        "i want", "i need", "i'd like", "i would like", "can i get",
        "can i have", "i'm looking for", "looking to", "want to book",
        "need to book", "would like to", "like to schedule", "need an",
        "want an", "get me", "book me", "schedule me", "set me up"
    ]
    
    # Expanded service keywords - check for any massage-related terms
    service_keywords = [
        "massage", "thai", "swedish", "deep tissue", "hot stone",
        "neck", "shoulder", "aromatherapy", "sports", "prenatal",
        "reflexology", "full body", "relaxation", "shiatsu", "trigger point",
        "lymphatic", "craniosacral", "myofascial", "cupping", "reiki",
        "couples", "chair", "foot", "back", "head", "scalp", "watsu",
        "lomi", "balinese", "ayurvedic", "indian head", "stone", "bamboo",
        "four hands", "postnatal", "geriatric", "oncology", "therapeutic",
        "stress relief", "energy healing", "meditation"
    ]
    
    pricing_keywords = ["price", "cost", "how much", "pricing", "fee", "charge", "rates"]
    status_keywords = ["status", "check", "view", "show", "my booking", "my appointments", "what do i have"]
    greeting_keywords = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    thanks_keywords = ["thanks", "thank you", "appreciate", "thank", "grateful"]

    # Only check booking intents if cancel/reschedule were not detected
    if not has_cancel and not has_reschedule:
        # Check for booking intent - many ways to express wanting to book
        # Pattern 1: Explicit booking keywords + service keywords
        has_booking_intent = any(word in query_lower for word in booking_keywords)
        has_service_mention = any(word in query_lower for word in service_keywords)
        
        # Pattern 2: Implicit booking (e.g., "I want a massage", "I need a swedish")
        implicit_booking_patterns = [
            "i want", "i need", "i'd like", "i would like", "can i get",
            "can i have", "i'm looking for", "looking to", "get me",
            "give me", "i'll take", "i'll have"
        ]
        has_implicit_booking = any(pattern in query_lower for pattern in implicit_booking_patterns)
        
        # Override intent based on keywords if model failed or for better accuracy
        # Pattern 1: Any booking intent (explicit or implicit) + service mention
        if (has_booking_intent or has_implicit_booking) and has_service_mention:
            state["intent"] = "book_service"
            state["response"] = "I'd be happy to help you book that massage!"
            state["confidence"] = 0.9
        # Pattern 2: Booking intent without service (they want to book something)
        elif has_booking_intent or has_implicit_booking:
            state["intent"] = "book_service"
            state["response"] = "I'd be happy to help you book a massage! What type would you like?"
            state["confidence"] = 0.85
    
    # Check other intents (pricing, status, greeting, thanks) if not already set
    if state.get("intent") not in ["cancel_booking", "reschedule_booking", "book_service"]:
        if any(word in query_lower for word in pricing_keywords):
            state["intent"] = "pricing_inquiry"
            state["response"] = "Let me check the prices."
            state["confidence"] = 0.85
        elif any(word in query_lower for word in status_keywords):
            state["intent"] = "booking_status"
            state["response"] = "Please provide your booking reference."
            state["confidence"] = 0.85
        elif any(word in query_lower for word in greeting_keywords):
            state["intent"] = "greeting"
            state["response"] = "Hello! How can I help with your booking?"
            state["confidence"] = 0.9
        elif any(word in query_lower for word in thanks_keywords):
            state["intent"] = "thanks"
            state["response"] = "You're welcome!"
            state["confidence"] = 0.9

    # Check conversation state for pending actions
    conv_state = state.get("conversation_state", {})
    
    # If we're awaiting date/time for a booking, check if user provided it FIRST
    # This should override other intents since we're completing a booking
    if conv_state.get("pending_service"):
        # Try to extract datetime from the message
        try:
            extracted_datetime = tool.extract_datetime(state["query"])
            if extracted_datetime:
                # User provided date/time - treat as booking intent (override any other intent)
                state["intent"] = "book_service"
                state["confidence"] = 0.9
        except Exception:
            pass
        # If no datetime found, the intent will remain as detected, and appointment_trigger will ask again
    
    # If we're awaiting date/time for a reschedule, check if user provided it
    if conv_state.get("pending_reschedule_id"):
        # Try to extract datetime from the message
        try:
            extracted_datetime = tool.extract_datetime(state["query"])
            if extracted_datetime:
                # User provided date/time - treat as reschedule intent (override any other intent)
                state["intent"] = "reschedule_booking"
                state["confidence"] = 0.9
        except Exception:
            pass
    
    # If we're awaiting a booking ID, check if user provided one
    if conv_state.get("awaiting_booking_id"):
        extracted_id = appt_tool.extract_booking_id_from_text(state["query"])
        if extracted_id:
            # User provided booking ID - maintain the original intent
            if conv_state.get("awaiting_booking_id") == "cancel":
                state["intent"] = "cancel_booking"
            elif conv_state.get("awaiting_booking_id") == "reschedule":
                state["intent"] = "reschedule_booking"
        # If no booking ID found, keep asking (handled in appointment_trigger)
    
    if conv_state.get("pending") == "reschedule":
        state["intent"] = "provide_datetime"
        state["response"] = "Noted the time."

    return state


def data_retrieval(state: ChatState):
    if state["intent"] == "pricing_inquiry":
        rag_result = rag_tool.retrieve_and_generate(state["query"])
        state["response"] = rag_result
    return state


def appointment_trigger(state: ChatState):
    user_id = state.get("conversation_state", {}).get("user_id", "user123")

    if state["intent"] in [
        "book_service",
        "reschedule_booking",
        "cancel_booking",
    ]:
        state["appointment_action"] = state["intent"]
        # Try to extract datetime, handle errors gracefully
        try:
            state["datetime"] = (
                tool.extract_datetime(state["query"]) or "Not extracted"
            )
        except Exception:
            state["datetime"] = "Not extracted"

        if state["intent"] == "book_service":
            # Extract service type from query - comprehensive matching
            query_lower = state["query"].lower()
            service = "Swedish Massage"  # Default to most common
            
            # Comprehensive service type detection (ordered by specificity)
            # Multi-word matches first (more specific)
            if "hot stone" in query_lower:
                service = "Hot Stone Massage"
            elif "deep tissue" in query_lower:
                service = "Deep Tissue Massage"
            elif "neck and shoulder" in query_lower or ("neck" in query_lower and "shoulder" in query_lower):
                service = "Neck and Shoulder Massage"
            elif "full body" in query_lower or "full body relaxation" in query_lower:
                service = "Full Body Relaxation"
            elif "aromatherapy" in query_lower:
                service = "Aromatherapy Massage"
            elif "hot stone" in query_lower:
                service = "Hot Stone Massage"
            elif "sports" in query_lower:
                service = "Sports Massage"
            elif "prenatal" in query_lower:
                service = "Prenatal Massage"
            elif "postnatal" in query_lower:
                service = "Postnatal Massage"
            elif "thai" in query_lower:
                service = "Thai Massage"
            elif "swedish" in query_lower:
                service = "Swedish Massage"
            elif "reflexology" in query_lower:
                service = "Reflexology"
            elif "shiatsu" in query_lower:
                service = "Shiatsu Massage"
            elif "trigger point" in query_lower:
                service = "Trigger Point Massage"
            elif "lymphatic" in query_lower or "lymphatic drainage" in query_lower:
                service = "Lymphatic Drainage Massage"
            elif "craniosacral" in query_lower:
                service = "Craniosacral Therapy"
            elif "myofascial" in query_lower:
                service = "Myofascial Release"
            elif "cupping" in query_lower:
                service = "Cupping Therapy"
            elif "reiki" in query_lower:
                service = "Reiki Massage"
            elif "couples" in query_lower:
                service = "Couples Massage"
            elif "chair" in query_lower:
                service = "Chair Massage"
            elif "foot" in query_lower:
                service = "Foot Massage"
            elif "back" in query_lower:
                service = "Back Massage"
            elif ("head" in query_lower and "scalp" in query_lower) or "scalp" in query_lower:
                service = "Head and Scalp Massage"
            elif "watsu" in query_lower:
                service = "Watsu Massage"
            elif "lomi lomi" in query_lower or "lomi" in query_lower:
                service = "Lomi Lomi Massage"
            elif "balinese" in query_lower:
                service = "Balinese Massage"
            elif "ayurvedic" in query_lower:
                service = "Ayurvedic Massage"
            elif "indian head" in query_lower:
                service = "Indian Head Massage"
            elif "stone" in query_lower and "hot" not in query_lower:
                service = "Stone Massage"
            elif "bamboo" in query_lower:
                service = "Warm Bamboo Massage"
            elif "four hands" in query_lower:
                service = "Four Hands Massage"
            elif "geriatric" in query_lower:
                service = "Geriatric Massage"
            elif "oncology" in query_lower:
                service = "Oncology Massage"
            elif "therapeutic" in query_lower:
                service = "Therapeutic Massage"
            elif "relaxation" in query_lower:
                service = "Relaxation Massage"
            elif "stress relief" in query_lower or "stress" in query_lower:
                service = "Stress Relief Massage"
            elif "energy healing" in query_lower:
                service = "Energy Healing Massage"
            elif "meditation" in query_lower:
                service = "Meditation Massage"
            elif "neck" in query_lower:
                service = "Neck and Shoulder Massage"
            elif "shoulder" in query_lower:
                service = "Neck and Shoulder Massage"

            # Check if datetime was extracted
            conv_state = state.get("conversation_state", {})
            
            # Check if we're completing a booking that was waiting for datetime
            if conv_state.get("pending_service") and state["datetime"] != "Not extracted":
                # Complete the booking with the stored service and new datetime
                service = conv_state["pending_service"]
                result = appt_tool.add_appointment(
                    user_id, service, state["datetime"]
                )
                appointments = appt_tool.get_appointments(user_id)
                latest_appt_id = (
                    max([appt[0] for appt in appointments]) if appointments else 1
                )
                booking_id = appt_tool.format_booking_id(latest_appt_id)
                state["response"] = (
                    f"Great! Appointment {booking_id} booked successfully for {service} on {state['datetime']}."
                )
                # Clear the pending service
                conv_state.pop("pending_service", None)
                state["conversation_state"] = conv_state
            elif state["datetime"] == "Not extracted":
                # No datetime provided - ask for it
                state["response"] = (
                    f"I'd be happy to book a {service} for you! "
                    f"Please provide the date and time (e.g., 'December 10th at 2 PM' or 'tomorrow at 3:00 PM')."
                )
                # Store the service in conversation state
                conv_state["pending_service"] = service
                state["conversation_state"] = conv_state
            else:
                # Datetime was extracted - proceed with booking
                result = appt_tool.add_appointment(
                    user_id, service, state["datetime"]
                )
                appointments = appt_tool.get_appointments(user_id)
                latest_appt_id = (
                    max([appt[0] for appt in appointments]) if appointments else 1
                )
                booking_id = appt_tool.format_booking_id(latest_appt_id)
                state["response"] = (
                    f"Great! Appointment {booking_id} booked successfully for {service} on {state['datetime']}."
                )

        elif state["intent"] == "reschedule_booking":
            appointments = appt_tool.get_appointments(user_id)
            pending_appointments = [
                appt for appt in appointments if appt[4] == "pending"
            ]
            
            # Extract booking ID from the query
            extracted_id = appt_tool.extract_booking_id_from_text(state["query"])
            conv_state = state.get("conversation_state", {})
            
            # Check if we have a pending reschedule ID (user was asked for datetime)
            pending_reschedule_id = conv_state.get("pending_reschedule_id")
            if pending_reschedule_id and state["datetime"] != "Not extracted":
                # User provided datetime for pending reschedule - complete it
                result = appt_tool.reschedule_appointment(pending_reschedule_id, state["datetime"])
                booking_id = appt_tool.format_booking_id(pending_reschedule_id)
                state["response"] = (
                    f"Appointment {booking_id} rescheduled successfully to {state['datetime']}."
                )
                conv_state.pop("pending_reschedule_id", None)
                state["conversation_state"] = conv_state
            elif not pending_appointments:
                state["response"] = "No pending appointments found to reschedule."
            elif len(pending_appointments) == 1:
                # Only one appointment - reschedule it directly if datetime provided
                appointment_id = pending_appointments[0][0]
                booking_id = appt_tool.format_booking_id(appointment_id)
                
                if state["datetime"] != "Not extracted":
                    result = appt_tool.reschedule_appointment(
                        appointment_id, state["datetime"]
                    )
                    state["response"] = (
                        f"Appointment {booking_id} rescheduled successfully to {state['datetime']}."
                    )
                else:
                    # No datetime provided - ask for it
                    state["response"] = (
                        f"Please provide the new date and time for appointment {booking_id} "
                        f"(e.g., 'December 10th at 3 PM' or 'tomorrow at 2:00 PM')."
                    )
                    conv_state["pending_reschedule_id"] = appointment_id
                    state["conversation_state"] = conv_state
            else:
                # Multiple appointments - check if booking ID was provided
                if conv_state.get("awaiting_booking_id") == "reschedule":
                    # User provided booking ID in follow-up message
                    if extracted_id:
                        found_appt = None
                        for appt in pending_appointments:
                            if appt[0] == extracted_id:
                                found_appt = appt
                                break
                        
                        if found_appt:
                            if state["datetime"] != "Not extracted":
                                result = appt_tool.reschedule_appointment(extracted_id, state["datetime"])
                                booking_id = appt_tool.format_booking_id(extracted_id)
                                state["response"] = f"Appointment {booking_id} rescheduled successfully to {state['datetime']}."
                                conv_state.pop("awaiting_booking_id", None)
                                state["conversation_state"] = conv_state
                            else:
                                booking_id = appt_tool.format_booking_id(extracted_id)
                                state["response"] = (
                                    f"Please provide the new date and time for appointment {booking_id} "
                                    f"(e.g., 'December 10th at 3 PM')."
                                )
                                conv_state["pending_reschedule_id"] = extracted_id
                                state["conversation_state"] = conv_state
                        else:
                            booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                            state["response"] = (
                                f"Booking ID {appt_tool.format_booking_id(extracted_id)} not found. "
                                f"Your pending appointments are: {', '.join(booking_ids)}."
                            )
                    else:
                        booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                        state["response"] = (
                            f"You have multiple pending appointments: {', '.join(booking_ids)}. "
                            f"Please provide the booking ID you'd like to reschedule."
                        )
                elif extracted_id:
                    # Booking ID found in initial reschedule request
                    found_appt = None
                    for appt in pending_appointments:
                        if appt[0] == extracted_id:
                            found_appt = appt
                            break
                    
                    if found_appt:
                        if state["datetime"] != "Not extracted":
                            result = appt_tool.reschedule_appointment(extracted_id, state["datetime"])
                            booking_id = appt_tool.format_booking_id(extracted_id)
                            state["response"] = f"Appointment {booking_id} rescheduled successfully to {state['datetime']}."
                        else:
                            booking_id = appt_tool.format_booking_id(extracted_id)
                            state["response"] = (
                                f"Please provide the new date and time for appointment {booking_id} "
                                f"(e.g., 'December 10th at 3 PM')."
                            )
                            conv_state["pending_reschedule_id"] = extracted_id
                            state["conversation_state"] = conv_state
                    else:
                        booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                        state["response"] = (
                            f"Booking ID {appt_tool.format_booking_id(extracted_id)} not found. "
                            f"Your pending appointments are: {', '.join(booking_ids)}."
                        )
                else:
                    # No booking ID provided - ask for it
                    booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                    state["response"] = (
                        f"You have multiple pending appointments: {', '.join(booking_ids)}. "
                        f"Please provide the booking ID you'd like to reschedule (e.g., BOOK-01-2025)."
                    )
                    conv_state["awaiting_booking_id"] = "reschedule"
                    state["conversation_state"] = conv_state

        elif state["intent"] == "cancel_booking":
            appointments = appt_tool.get_appointments(user_id)
            pending_appointments = [
                appt for appt in appointments if appt[4] == "pending"
            ]
            
            if not pending_appointments:
                state["response"] = "No pending appointments found to cancel."
            elif len(pending_appointments) == 1:
                # Only one appointment - cancel it directly
                appointment_id = pending_appointments[0][0]
                booking_id = appt_tool.format_booking_id(appointment_id)
                result = appt_tool.cancel_appointment(appointment_id)
                state["response"] = f"Appointment {booking_id} cancelled successfully."
            else:
                # Multiple appointments - check if booking ID was provided
                query_lower = state["query"].lower()
                extracted_id = appt_tool.extract_booking_id_from_text(state["query"])
                
                # Check conversation state to see if we're waiting for booking ID
                conv_state = state.get("conversation_state", {})
                if conv_state.get("awaiting_booking_id") == "cancel":
                    # User provided booking ID in follow-up message
                    if extracted_id:
                        # Find appointment by ID
                        found_appt = None
                        for appt in pending_appointments:
                            if appt[0] == extracted_id:
                                found_appt = appt
                                break
                        
                        if found_appt:
                            result = appt_tool.cancel_appointment(extracted_id)
                            booking_id = appt_tool.format_booking_id(extracted_id)
                            state["response"] = f"Appointment {booking_id} cancelled successfully."
                            # Clear the awaiting state
                            conv_state.pop("awaiting_booking_id", None)
                            state["conversation_state"] = conv_state
                        else:
                            booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                            state["response"] = (
                                f"Booking ID {appt_tool.format_booking_id(extracted_id)} not found. "
                                f"Your pending appointments are: {', '.join(booking_ids)}. "
                                f"Please provide a valid booking ID."
                            )
                    else:
                        # Still no booking ID provided
                        booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                        state["response"] = (
                            f"You have multiple pending appointments: {', '.join(booking_ids)}. "
                            f"Please provide the booking ID you'd like to cancel (e.g., BOOK-01-2025)."
                        )
                elif extracted_id:
                    # Booking ID found in initial cancel request
                    found_appt = None
                    for appt in pending_appointments:
                        if appt[0] == extracted_id:
                            found_appt = appt
                            break
                    
                    if found_appt:
                        result = appt_tool.cancel_appointment(extracted_id)
                        booking_id = appt_tool.format_booking_id(extracted_id)
                        state["response"] = f"Appointment {booking_id} cancelled successfully."
                    else:
                        booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                        state["response"] = (
                            f"Booking ID {appt_tool.format_booking_id(extracted_id)} not found. "
                            f"Your pending appointments are: {', '.join(booking_ids)}. "
                            f"Please provide a valid booking ID."
                        )
                else:
                    # No booking ID provided - ask for it
                    booking_ids = [appt_tool.format_booking_id(appt[0]) for appt in pending_appointments]
                    state["response"] = (
                        f"You have multiple pending appointments: {', '.join(booking_ids)}. "
                        f"Please provide the booking ID you'd like to cancel (e.g., BOOK-01-2025)."
                    )
                    # Set conversation state to await booking ID
                    conv_state["awaiting_booking_id"] = "cancel"
                    state["conversation_state"] = conv_state

    elif state["intent"] == "booking_status":
        appointments = appt_tool.get_appointments(user_id)
        if appointments:
            count = len(appointments)
            latest = appointments[-1]
            booking_id = appt_tool.format_booking_id(latest[0])
            state["response"] = (
                f"You have {count} booking(s). Your most recent: {booking_id} - {latest[2]} on {latest[3]} (Status: {latest[4]})"
            )
        else:
            state["response"] = "You have no bookings yet."
    elif state["intent"] == "confirm":
        if state.get("conversation_state", {}).get("pending") == "reschedule":
            # Perform reschedule
            result = appt_tool.reschedule_appointment(1, state["datetime"])
            state["response"] = (
                f"Sent reschedule information to pro, you will get notified once it's confirmed. {result}"
            )
            state["conversation_state"] = {}
    return state


# Build graph
graph = StateGraph(ChatState)
graph.add_node("intent_analysis", intent_analysis)
graph.add_node("data_retrieval", data_retrieval)
graph.add_node("appointment_trigger", appointment_trigger)
graph.add_edge(START, "intent_analysis")
graph.add_edge("intent_analysis", "data_retrieval")
graph.add_edge("data_retrieval", "appointment_trigger")
graph.add_edge("appointment_trigger", END)

# Compile and run
compiled_graph = graph.compile()

# Example usage
if __name__ == "__main__":
    state = {"query": "Can I reschedule my booking?", "conversation_state": {}}
    result = compiled_graph.invoke(state)
    print(result)