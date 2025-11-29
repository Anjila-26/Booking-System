#!/usr/bin/env python3
"""
Chatbot Test Script
Tests all intents and features of the booking chatbot.
"""

import sys
import os

# Add the backend app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.chatbot_workflow import compiled_graph
from app.tools.appointment_tool import AppointmentTool
import uuid


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_test_header(test_name):
    """Print a formatted test header"""
    print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}Test: {test_name}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")


def print_user_message(message):
    """Print user message"""
    print(f"\n{Colors.BLUE}User:{Colors.RESET} {message}")


def print_bot_response(response_data):
    """Print bot response with details"""
    print(f"{Colors.GREEN}Bot:{Colors.RESET} {response_data.get('response', 'N/A')}")
    print(f"  {Colors.YELLOW}Intent:{Colors.RESET} {response_data.get('intent', 'N/A')}")
    print(f"  {Colors.YELLOW}Confidence:{Colors.RESET} {response_data.get('confidence', 0):.2%}")


def run_test(test_name, user_message, expected_intent=None, user_id=None, conversation_state=None):
    """Run a single test case"""
    print_test_header(test_name)
    print_user_message(user_message)
    
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    if conversation_state is None:
        conversation_state = {}
    
    try:
        state = {
            "query": user_message,
            "conversation_state": {**conversation_state, "user_id": user_id},
        }
        
        result = compiled_graph.invoke(state)
        print_bot_response(result)
        
        # Verify intent if expected
        if expected_intent:
            actual_intent = result.get("intent", "")
            if actual_intent == expected_intent:
                print(f"{Colors.GREEN}✓ Intent matches expected: {expected_intent}{Colors.RESET}")
            else:
                print(f"{Colors.RED}✗ Intent mismatch! Expected: {expected_intent}, Got: {actual_intent}{Colors.RESET}")
        
        return result
    except Exception as e:
        print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all test scenarios"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print("CHATBOT COMPREHENSIVE TEST SUITE")
    print(f"{'='*70}{Colors.RESET}\n")
    
    # Use a consistent user ID for testing
    test_user_id = "test_user_123"
    conversation_state = {}
    
    # Clean up any existing test appointments
    print(f"{Colors.YELLOW}Cleaning up test data...{Colors.RESET}")
    try:
        appt_tool = AppointmentTool()
        appt_tool._ensure_initialized()
        # Note: In production, you'd want to clean up test appointments
    except:
        pass
    
    # Test 1: Greeting
    result = run_test(
        "Greeting",
        "Hello",
        expected_intent="greeting"
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 2: Booking - Explicit
    result = run_test(
        "Booking - Explicit Request",
        "Book me a Swedish massage for December 5th at 2 PM",
        expected_intent="book_service",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 3: Booking - Implicit
    result = run_test(
        "Booking - Implicit Request",
        "I want a deep tissue massage",
        expected_intent="book_service",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 4: Pricing Inquiry
    result = run_test(
        "Pricing Inquiry",
        "How much does a Swedish massage cost?",
        expected_intent="pricing_inquiry",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 5: Booking Status
    result = run_test(
        "Booking Status",
        "Show me my bookings",
        expected_intent="booking_status",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 6: Booking Another Appointment
    result = run_test(
        "Booking - Second Appointment",
        "Book me a Thai massage for December 10th at 3 PM",
        expected_intent="book_service",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 7: Cancellation - Multiple Appointments (should ask for ID)
    result = run_test(
        "Cancellation - Multiple Appointments",
        "Cancel my appointment",
        expected_intent="cancel_booking",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 8: Provide Booking ID for Cancellation
    if conversation_state.get("awaiting_booking_id") == "cancel":
        result = run_test(
            "Cancellation - Provide Booking ID",
            "BOOK-01-2025",
            expected_intent="cancel_booking",
            user_id=test_user_id,
            conversation_state=conversation_state
        )
        conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 9: Cancellation with ID in Message
    result = run_test(
        "Cancellation - ID in Message",
        "Cancel BOOK-02-2025",
        expected_intent="cancel_booking",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 10: Rescheduling
    result = run_test(
        "Rescheduling",
        "Reschedule my appointment to December 15th at 4 PM",
        expected_intent="reschedule_booking",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 11: Thanks
    result = run_test(
        "Thanks",
        "Thank you",
        expected_intent="thanks",
        user_id=test_user_id,
        conversation_state=conversation_state
    )
    conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 12: Various Service Types
    service_tests = [
        ("Hot Stone Massage", "Book me a hot stone massage"),
        ("Aromatherapy Massage", "I want an aromatherapy massage"),
        ("Sports Massage", "Schedule a sports massage"),
        ("Prenatal Massage", "I need a prenatal massage"),
    ]
    
    for service_name, message in service_tests:
        result = run_test(
            f"Service Type - {service_name}",
            message,
            expected_intent="book_service",
            user_id=test_user_id,
            conversation_state=conversation_state
        )
        conversation_state = result.get("conversation_state", {}) if result else {}
    
    # Test 13: Edge Cases
    edge_cases = [
        ("Cancel Variation", "cancel", "cancel_booking"),
        ("Cancel with Question Mark", "cancel?", "cancel_booking"),
        ("Reschedule Variation", "Change my appointment", "reschedule_booking"),
        ("Remove Booking", "Remove my booking", "cancel_booking"),
    ]
    
    for test_name, message, expected_intent in edge_cases:
        result = run_test(
            f"Edge Case - {test_name}",
            message,
            expected_intent=expected_intent,
            user_id=test_user_id,
            conversation_state=conversation_state
        )
        conversation_state = result.get("conversation_state", {}) if result else {}
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*70}")
    print("TEST SUITE COMPLETED")
    print(f"{'='*70}{Colors.RESET}\n")
    
    # Show final appointment status
    print(f"{Colors.CYAN}Final Appointment Status:{Colors.RESET}")
    try:
        appt_tool = AppointmentTool()
        appt_tool._ensure_initialized()
        appointments = appt_tool.get_appointments(test_user_id)
        if appointments:
            for appt in appointments:
                booking_id = appt_tool.format_booking_id(appt[0])
                print(f"  {booking_id} - {appt[2]} on {appt[3]} (Status: {appt[4]})")
        else:
            print("  No appointments found")
    except Exception as e:
        print(f"  Error retrieving appointments: {e}")


if __name__ == "__main__":
    main()

