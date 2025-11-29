# Chatbot Test Flow - Complete Intent Coverage

This document provides a comprehensive test flow to verify all chatbot intents and features are working correctly.

## Test Scenario 1: Greeting & Initial Interaction

**User:** `Hello`
**Expected Bot Response:**
- Intent: `greeting`
- Response: "Hello! How can I help with your booking?"
- Confidence: ~0.9

---

## Test Scenario 2: Booking - Explicit Booking Request

**User:** `Book me a Swedish massage for December 5th at 2 PM`
**Expected Bot Response:**
- Intent: `book_service`
- Response: "Great! Appointment BOOK-01-2025 booked successfully for Swedish Massage on 2025-12-05 14:00."
- Creates appointment with booking ID format: BOOK-01-2025

---

## Test Scenario 3: Booking - Implicit Booking Request

**User:** `I want a deep tissue massage`
**Expected Bot Response:**
- Intent: `book_service`
- Response: "I'd be happy to help you book that massage!"
- May ask for date/time if not provided

---

## Test Scenario 4: Booking - Different Service Types

**User:** `Can I get a Thai massage for tomorrow at 10 AM?`
**Expected Bot Response:**
- Intent: `book_service`
- Response: "Great! Appointment BOOK-02-2025 booked successfully for Thai Massage on [tomorrow's date] 10:00."
- Booking ID: BOOK-02-2025

**User:** `Schedule me a hot stone massage`
**Expected Bot Response:**
- Intent: `book_service`
- Response: "I'd be happy to help you book that massage!"
- Service: Hot Stone Massage

**User:** `I need a neck and shoulder massage`
**Expected Bot Response:**
- Intent: `book_service`
- Service: Neck and Shoulder Massage

---

## Test Scenario 5: Pricing Inquiry

**User:** `How much does a Swedish massage cost?`
**Expected Bot Response:**
- Intent: `pricing_inquiry`
- Response: "The Swedish Massage costs $80 and lasts for 60 minutes."
- Uses data_tool to retrieve pricing from dataset

**User:** `What's the price of a Thai massage?`
**Expected Bot Response:**
- Intent: `pricing_inquiry`
- Response: "The Thai Massage costs $100 and lasts for 75 minutes."

**User:** `How much for deep tissue?`
**Expected Bot Response:**
- Intent: `pricing_inquiry`
- Response: "The Deep Tissue Massage costs $95 and lasts for 60 minutes."

---

## Test Scenario 6: Booking Status Check

**User:** `Show me my bookings`
**Expected Bot Response:**
- Intent: `booking_status`
- Response: "You have X booking(s). Your most recent: BOOK-XX-2025 - [Service] on [Date] (Status: pending)"
- Shows all appointments with booking IDs

**User:** `What appointments do I have?`
**Expected Bot Response:**
- Intent: `booking_status`
- Lists all appointments

---

## Test Scenario 7: Cancellation - Single Appointment

**Setup:** User has only 1 pending appointment (BOOK-01-2025)

**User:** `I want to cancel my appointment`
**Expected Bot Response:**
- Intent: `cancel_booking`
- Response: "Appointment BOOK-01-2025 cancelled successfully."
- Cancels immediately without asking for ID

---

## Test Scenario 8: Cancellation - Multiple Appointments (No ID Provided)

**Setup:** User has 3 pending appointments:
- BOOK-01-2025 - Deep Tissue Massage
- BOOK-02-2025 - Thai Massage  
- BOOK-03-2025 - Swedish Massage

**User:** `Cancel my appointment`
**Expected Bot Response:**
- Intent: `cancel_booking`
- Response: "You have multiple pending appointments: BOOK-01-2025, BOOK-02-2025, BOOK-03-2025. Please provide the booking ID you'd like to cancel (e.g., BOOK-01-2025)."
- Sets conversation state: `awaiting_booking_id: "cancel"`

**User:** `BOOK-02-2025`
**Expected Bot Response:**
- Intent: `cancel_booking` (maintained from conversation state)
- Response: "Appointment BOOK-02-2025 cancelled successfully."
- Clears `awaiting_booking_id` from conversation state

---

## Test Scenario 9: Cancellation - Booking ID in Initial Request

**Setup:** User has multiple appointments

**User:** `Cancel BOOK-01-2025`
**Expected Bot Response:**
- Intent: `cancel_booking`
- Response: "Appointment BOOK-01-2025 cancelled successfully."
- Extracts booking ID from message and cancels directly

**User:** `I want to cancel booking BOOK-03-2025`
**Expected Bot Response:**
- Intent: `cancel_booking`
- Response: "Appointment BOOK-03-2025 cancelled successfully."

---

## Test Scenario 10: Cancellation - Invalid Booking ID

**Setup:** User has appointments BOOK-01-2025 and BOOK-02-2025

**User:** `Cancel BOOK-99-2025`
**Expected Bot Response:**
- Intent: `cancel_booking`
- Response: "Booking ID BOOK-99-2025 not found. Your pending appointments are: BOOK-01-2025, BOOK-02-2025. Please provide a valid booking ID."

---

## Test Scenario 11: Rescheduling - Single Appointment

**Setup:** User has 1 pending appointment

**User:** `I need to reschedule my appointment to December 10th at 3 PM`
**Expected Bot Response:**
- Intent: `reschedule_booking`
- Response: "Appointment BOOK-01-2025 rescheduled successfully to 2025-12-10 15:00."
- Reschedules immediately

---

## Test Scenario 12: Rescheduling - Multiple Appointments (No ID)

**Setup:** User has multiple appointments

**User:** `Reschedule my appointment`
**Expected Bot Response:**
- Intent: `reschedule_booking`
- Response: "You have multiple pending appointments: BOOK-01-2025, BOOK-02-2025. Please provide the booking ID you'd like to reschedule (e.g., BOOK-01-2025)."
- Sets conversation state: `awaiting_booking_id: "reschedule"`

**User:** `BOOK-01-2025 to December 15th at 4 PM`
**Expected Bot Response:**
- Intent: `reschedule_booking`
- Response: "Appointment BOOK-01-2025 rescheduled successfully to 2025-12-15 16:00."

---

## Test Scenario 13: Rescheduling - Booking ID in Initial Request

**User:** `Reschedule BOOK-02-2025 to next Monday at 2 PM`
**Expected Bot Response:**
- Intent: `reschedule_booking`
- Response: "Appointment BOOK-02-2025 rescheduled successfully to [next Monday's date] 14:00."

---

## Test Scenario 14: Various Booking Phrases

**User:** `Schedule me an appointment for a Swedish massage`
**Expected Bot Response:**
- Intent: `book_service`
- Service: Swedish Massage

**User:** `I'd like to book a deep tissue massage`
**Expected Bot Response:**
- Intent: `book_service`
- Service: Deep Tissue Massage

**User:** `Can I get a hot stone massage?`
**Expected Bot Response:**
- Intent: `book_service`
- Service: Hot Stone Massage

**User:** `Set up a Thai massage for me`
**Expected Bot Response:**
- Intent: `book_service`
- Service: Thai Massage

**User:** `I need an aromatherapy massage`
**Expected Bot Response:**
- Intent: `book_service`
- Service: Aromatherapy Massage

---

## Test Scenario 15: Thanks & Politeness

**User:** `Thank you`
**Expected Bot Response:**
- Intent: `thanks`
- Response: "You're welcome!"
- Confidence: ~0.9

**User:** `Thanks for your help`
**Expected Bot Response:**
- Intent: `thanks`
- Response: "You're welcome!"

---

## Test Scenario 16: Complex Booking with Date/Time Extraction

**User:** `Book me a sports massage for January 20th, 2025 at 11:30 AM`
**Expected Bot Response:**
- Intent: `book_service`
- Response: "Great! Appointment BOOK-XX-2025 booked successfully for Sports Massage on 2025-01-20 11:30."
- Correctly extracts date and time

**User:** `I want a prenatal massage tomorrow at 9:00`
**Expected Bot Response:**
- Intent: `book_service`
- Service: Prenatal Massage
- Date: Tomorrow's date
- Time: 09:00

---

## Test Scenario 17: Edge Cases - Cancel Variations

**User:** `cancel`
**Expected Bot Response:**
- Intent: `cancel_booking`
- If multiple: Asks for booking ID
- If single: Cancels directly

**User:** `cancel?`
**Expected Bot Response:**
- Intent: `cancel_booking`
- Handles question mark

**User:** `I want to cancel`
**Expected Bot Response:**
- Intent: `cancel_booking`

**User:** `Remove my booking`
**Expected Bot Response:**
- Intent: `cancel_booking`
- "remove" is a cancel keyword

---

## Test Scenario 18: Edge Cases - Reschedule Variations

**User:** `Change my appointment`
**Expected Bot Response:**
- Intent: `reschedule_booking`
- "change" is a reschedule keyword

**User:** `Modify my booking`
**Expected Bot Response:**
- Intent: `reschedule_booking`
- "modify" is a reschedule keyword

**User:** `Move my appointment to next week`
**Expected Bot Response:**
- Intent: `reschedule_booking`
- "move" is a reschedule keyword

---

## Test Scenario 19: Service Type Detection - Comprehensive

**User:** `Book a reflexology session`
**Expected Bot Response:**
- Service: Reflexology

**User:** `I want a couples massage`
**Expected Bot Response:**
- Service: Couples Massage

**User:** `Schedule a foot massage`
**Expected Bot Response:**
- Service: Foot Massage

**User:** `Book me a shiatsu massage`
**Expected Bot Response:**
- Service: Shiatsu Massage

**User:** `I need a full body relaxation`
**Expected Bot Response:**
- Service: Full Body Relaxation

---

## Test Scenario 20: Complete Conversation Flow

**User:** `Hello`
**Bot:** "Hello! How can I help with your booking?"

**User:** `I want to book a Swedish massage for December 10th at 2 PM`
**Bot:** "Great! Appointment BOOK-01-2025 booked successfully for Swedish Massage on 2025-12-10 14:00."

**User:** `How much does a Thai massage cost?`
**Bot:** "The Thai Massage costs $100 and lasts for 75 minutes."

**User:** `Book me a Thai massage for December 12th at 3 PM`
**Bot:** "Great! Appointment BOOK-02-2025 booked successfully for Thai Massage on 2025-12-12 15:00."

**User:** `Show me my appointments`
**Bot:** "You have 2 booking(s). Your most recent: BOOK-02-2025 - Thai Massage on 2025-12-12 (Status: pending)"

**User:** `Cancel my appointment`
**Bot:** "You have multiple pending appointments: BOOK-01-2025, BOOK-02-2025. Please provide the booking ID you'd like to cancel (e.g., BOOK-01-2025)."

**User:** `BOOK-01-2025`
**Bot:** "Appointment BOOK-01-2025 cancelled successfully."

**User:** `Reschedule BOOK-02-2025 to December 15th at 4 PM`
**Bot:** "Appointment BOOK-02-2025 rescheduled successfully to 2025-12-15 16:00."

**User:** `Thank you`
**Bot:** "You're welcome!"

---

## Test Scenario 21: Booking ID Format Verification

After each booking, verify:
- ✅ Booking ID format: `BOOK-XX-YYYY` (e.g., BOOK-01-2025)
- ✅ Sequential numbering (BOOK-01, BOOK-02, BOOK-03, etc.)
- ✅ Year matches current year
- ✅ Zero-padded numbers (01, 02, not 1, 2)

---

## Test Scenario 22: Error Handling

**User:** `Cancel BOOK-99-2025` (non-existent ID)
**Expected Bot Response:**
- Lists available booking IDs
- Asks for valid booking ID

**User:** `Book me a massage` (no service type specified)
**Expected Bot Response:**
- Intent: `book_service`
- Response: "I'd be happy to help you book a massage! What type would you like?"

**User:** `Book me a massage` (no date/time)
**Expected Bot Response:**
- Creates booking with "Not extracted" datetime
- Or asks for date/time (depending on implementation)

---

## Verification Checklist

After running through all scenarios, verify:

- [ ] All intents are detected correctly
- [ ] Booking IDs are formatted as BOOK-XX-YYYY
- [ ] Single appointment cancellation works without asking for ID
- [ ] Multiple appointment cancellation asks for booking ID
- [ ] Booking ID extraction works from various formats
- [ ] Rescheduling works for single and multiple appointments
- [ ] Pricing inquiries retrieve correct data from dataset
- [ ] Status checks show all appointments with booking IDs
- [ ] Greetings and thanks are handled appropriately
- [ ] Service type detection works for all massage types
- [ ] Date/time extraction works correctly
- [ ] Conversation state is maintained properly
- [ ] Error handling works for invalid inputs

---

## Notes

- All booking IDs follow format: `BOOK-{id:02d}-{year}`
- Booking IDs are sequential based on appointment creation order
- The system uses lazy initialization for all tools (model, database, dataset)
- Conversation state tracks `awaiting_booking_id` for multi-step operations
- Intent detection prioritizes cancel/reschedule over booking to avoid false matches

