import logging

from booking_information_validator import BookingInformationValidator
from state import State


class ChatControlMsg:
    def __init__(self):
        self.msg_to_user = None
        self.flag = None

    def __str__(self):
        return f"msg_to_user: {self.msg_to_user}, flag: {self.flag}"


class ControlFlowManager:
    """The control flow manager intervenes if the chat flow does not proceed as intended.
    It validates information given in the state object.
    Depending on the information given, it will show an error or the booking confirmation
    or do nothing"""
    booking_information_validator = BookingInformationValidator()

    def handle_state(self, state: State) -> ChatControlMsg:
        """Performs validation and analyses the chat state. It returns a dictionary
        that can contain a chat message to the user."""
        logging.info(f"Enter handle_state")

        validation_result = self.booking_information_validator.validate(state)
        if validation_result['has_error']:
            logging.info(f"Exit handle_state with validator error")
            response = ChatControlMsg()
            response.msg_to_user = validation_result['error_msg']
            return response

        user_just_confirmed_booking = state.booking_confirmed.value

        response = ChatControlMsg()

        if user_just_confirmed_booking:
            logging.info("Mock booking performed")
            response.msg_to_user = f"Thank you for choosing our hotel. A booking confirmation was sent to {state.email_address.raw_value}. Have a great day!"
            response.flag = 'booking_finished'
        logging.info(f"Exit handle_state: {response}")
        return response


