import logging

from booking_information_validator import BookingInformationValidator
from chat_gpt_adapter import ChatGptAdapter
from data_extractor import DataExtractor
from state import State


class ChatControlMsg:
    def __init__(self):
        self.msg_to_user = None
        self.msg_to_bot = None
        self.flag = None

    def __str__(self):
        return f"msg_to_user: {self.msg_to_user}, msg_to_bot: {self.msg_to_bot}, flag: {self.flag}"

class ControlFlowManager:
    """The control flow manager makes sure the chat proceeds as intended.
    It extracts and validates information given by ChatGPT in text form.
    Depending on the information given, it will show an error, a booking summary or the booking confirmation
    or do nothing"""
    booking_information_validator = BookingInformationValidator()
    data_extractor = DataExtractor()

    """ the state stores all relevant information for the hotel booking process """
    state = State()

    booking_form_query = """List all booking-relevant information already provided by me as table with exactly two columns 
        and 6 rows of the form:
                Date of arrival | <date of arrival>
                Duration of stay | <number of nights>
                Number of guests | <number of guests>
                Name of main guest | <name of main guest>
                Email address | <email address>
                Breakfast included? | <(yes|no)>
                Did I confirm a booking summary? | <(yes|no)>
                
                For any value not provided yet by me yet write [not provided] into the respective cells of the table.
                
                Use the pipe symbol (|) as seperator between keys and values.
                Remember: The table must have exactly two columns!
            """

    def _last_msg_query(self, last_bot_msg: str) -> str:
        return f"""Read the following text and answer a question referring to the text.
        Text: {last_bot_msg}
        End of text.

        Does the text above show a summary of a hotel booking including all of the following information: 
        date of arrival, 
        duration of stay, 
        name of guest, 
        number of guests? 
        
        Answer with yes or no.
        """

    def _create_booking_summary_msg(self, state: State) -> str:
        """Creates a string summarizing the booking information"""
        price_per_night = 100
        price_for_breakfast_per_night = 10 if state.breakfast_included.value else 0
        price = price_per_night * state.duration_of_stay.value
        price += state.number_of_guests.value * price_for_breakfast_per_night * state.duration_of_stay.value
        return f"""~ Booking summary ~ 
        
        Date of arrival: {state.date_of_arrival.raw_value}
        Duration of stay: {state.duration_of_stay.raw_value}
        Number of guests: {state.number_of_guests.raw_value}
        Name of main guest: {state.name_of_main_guest.raw_value}
        Breakfast included?: {state.breakfast_included.raw_value}
        Email address: {state.email_address.raw_value}
        
        Price: {"${:,.2f}".format(price)}
        
        Check in time: after 2pm
        Check out time: before 10am
        
        Do you wish to confirm the booking?"""

    def _find_missing_info(self, state: State) -> str:
        missing = list(filter(lambda entry: entry.value is None and entry.mandatory,
                              state.__dict__.values()))
        return missing[0].label if len(missing) > 0 else None

    def _query_chat_state_from_bot(self, next_msg_from_bot, messages: list, adapter: ChatGptAdapter) -> str:
        """Queries information about the chat history and last chat message from ChatGPT."""
        logging.debug('Enter _query_chat_state_from_bot')
        copy_of_chat = messages.copy()
        copy_of_chat.append({"role": "assistant", "content": next_msg_from_bot})
        copy_of_chat.append(
            {"role": "user", "content": self.booking_form_query})
        booking_info_table = adapter.chat_completion(copy_of_chat, 0.2)
        logging.info(booking_info_table)

        bot_is_showing_booking_summary = adapter.chat_completion(
            [{"role": "user", "content": self._last_msg_query(next_msg_from_bot)}], 0.2)

        logging.info("Does the bot want to show a booking summary? " + bot_is_showing_booking_summary)

        return booking_info_table + '\n' + f"Does the bot want to show a booking summary? | {bot_is_showing_booking_summary}"

    def handle_state(self, messages: list, next_msg_from_bot: str,
                     chat_gpt_adapter: ChatGptAdapter) -> ChatControlMsg:
        """Queries ChatGPT about the chat history, performs validation and returns a dictionary
        that can contain a chat message to the user or to ChatGTP itself."""
        logging.debug(f"Enter handle_state")
        chat_state_table = self._query_chat_state_from_bot(next_msg_from_bot, messages, chat_gpt_adapter)

        new_state = self.data_extractor.extract_values_from_chat_bot_response(chat_state_table)
        validation_result = self.booking_information_validator.validate(new_state)
        if validation_result['has_error']:
            logging.info(f"Exit handle_state with validator error")
            response = ChatControlMsg()
            response.msg_to_user = validation_result['error_msg']
            return response

        missing_info = self._find_missing_info(new_state)
        about_to_show_booking_summary = new_state.about_to_show_booking_summary.value
        user_just_confirmed_booking = new_state.booking_confirmed.value

        response = ChatControlMsg()

        if (about_to_show_booking_summary or user_just_confirmed_booking) and missing_info is not None:
            response.msg_to_bot = f"Ask the user for the following information: {missing_info}"
        elif user_just_confirmed_booking:
            response.msg_to_user = f"Thank you you for choosing our hotel. A booking confirmation was sent to {new_state.email_address.raw_value}. Have a great day!"
            response.flag = 'booking_finished'
        elif about_to_show_booking_summary:
            response.msg_to_user = self._create_booking_summary_msg(new_state)
        self.state = new_state
        logging.info(f"Exit handle_state: {response}")
        return response