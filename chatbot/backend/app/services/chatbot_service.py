from datetime import datetime
from typing import Any, Dict

from app.chatbot_workflow import compiled_graph
from app.models.schemas import ChatResponse


class ChatbotService:
    def __init__(self):
        self.compiled_graph = compiled_graph

    def process_message(
        self, message: str, user_id: str, conversation_state: Dict[str, Any]
    ) -> ChatResponse:
        try:
            # Prepare state for the LangGraph workflow
            state = {
                "query": message,
                "conversation_state": {**conversation_state, "user_id": user_id},
                "intent": "",
                "confidence": 0.0,
                "response": "",
                "appointment_action": "",
                "datetime": "",
            }

            # Invoke the compiled graph
            result = self.compiled_graph.invoke(state)

            # Ensure all required fields are present
            response_text = result.get("response", "I'm sorry, I didn't understand that.")
            intent = result.get("intent", "unknown")
            confidence = result.get("confidence", 0.5)
            conv_state = result.get("conversation_state", conversation_state)

            # Return the response in the expected format
            return ChatResponse(
                response=response_text,
                intent=intent,
                confidence=confidence,
                conversation_state=conv_state,
                timestamp=datetime.now(),
            )
        except Exception as e:
            # Fallback response if workflow fails completely
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            
            return ChatResponse(
                response="I encountered an error processing your message. Please try again or rephrase your question.",
                intent="error",
                confidence=0.0,
                conversation_state=conversation_state,
                timestamp=datetime.now(),
            )