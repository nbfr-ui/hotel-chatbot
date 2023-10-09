import json
import logging

from booking_information_validator import BookingInformationValidator
from chat_gpt_adapter import ChatGptAdapter
from data_extractor import DataExtractor
from state import State


class ChatControlMsg:
    def __init__(self):
        self.msg_to_user = None
        self.flag = None

    def __str__(self):
        return f"msg_to_user: {self.msg_to_user}, flag: {self.flag}"


class ControlFlowManager:
    """The control flow manager makes sure the chat proceeds as intended.
    It extracts and validates information given by ChatGPT in text form.
    Depending on the information given, it will show an error, a booking summary or the booking confirmation
    or do nothing"""
    booking_information_validator = BookingInformationValidator()
    data_extractor = DataExtractor()

    structured_data_query = """List all booking-relevant information already provided by the user as table with exactly two columns 
        and 7 rows of the form:
                Date of arrival | <date of arrival>
                Duration of stay | <number of nights>
                Number of guests | <number of guests>
                Name of main guest | <name of main guest>
                Email address | <email address>
                Breakfast included? | <(yes|no)>
                Did the user confirm a booking summary? | <(yes|no)>
                
                For any value not provided yet by me yet write [not provided] into the respective cells of the table.
                
                Use the pipe symbol (|) as seperator between keys and values.
                Remember: The table must have exactly two columns!
            """

    def extract_state(self, messages: list, next_msg_from_bot: str | None, chat_gpt_adapter: ChatGptAdapter) -> State:
        chat_state_table = self._query_chat_state_from_bot(next_msg_from_bot, messages, chat_gpt_adapter)
        return self.data_extractor.extract_values_from_chat_bot_response(chat_state_table)

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
            response.msg_to_user = f"Thank you for choosing our hotel. A booking confirmation was sent to {state.email_address.raw_value}. Have a great day!"
            response.flag = 'booking_finished'
        logging.info(f"Exit handle_state: {response}")
        return response

    def _query_chat_state_from_bot(self, next_msg_from_bot: str | None, messages: list, adapter: ChatGptAdapter) -> str:
        """Queries information about the chat history and last chat message from ChatGPT."""
        logging.info('Enter _query_chat_state_from_bot')
        copy_of_chat = messages.copy()
        if next_msg_from_bot is not None:
            copy_of_chat.append({"role": "assistant", "content": next_msg_from_bot})
        copy_of_chat.append(
            {"role": "user", "content": self.structured_data_query})

        # structured data from ChatGPT is requested via a fine-tuned model
        booking_info_table = adapter.chat_completion(copy_of_chat, None, 0.2, adapter.structured_query_model).content
        logging.info(booking_info_table)
        logging.debug(json.dumps(copy_of_chat + [{"role": "assistant", "content": booking_info_table}]))

        return booking_info_table

