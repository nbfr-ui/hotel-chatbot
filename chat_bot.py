import datetime
import logging

from chat_gpt_adapter import ChatGptAdapter
from control_flow_manager import ControlFlowManager
from price_calculator import calculate_price
from session_info import SessionInfo
from state import State

# this text provides context information about to hotel
hotel_information = """Name of the hotel: Hotel Royal
Address: Main square, Madrid, Spain
Check in time: 2pm, check out time: 10am.
Room sized: the hotel offers double bed standard rooms exclusively. The maximal number of guests for such a room is 3.
It is not possible to book for more than 3 guests. If there are more than 3 guests the user needs to make two separate bookings.
The guest can only book one room at a time. To book more rooms the user needs to start a second booking process.
Breakfast: $10 per guest per night. The breakfast offers orange and apple juice, bread, coffee, boiled eggs, cheese,
butter, honey and marmalade.
Facilities: a small gym and sauna.
Animals are not allowed.
Price per night: about $100. A accurate price will be given at the end of the booking process."""


class ChatBot:
    """The main interface of the chatbot."""

    control_flow_manager = ControlFlowManager()
    chat_gpt_adapter = ChatGptAdapter()

    def continue_chat(
            self,
            session_info: SessionInfo,
            messages: list,
    ) -> dict:
        """This method receives the chat history and generates a chat response"""
        logging.info(f"Enter continue_chat")

        session_info.state = self.control_flow_manager.extract_state(messages, None,
                                                                     self.chat_gpt_adapter)

        system_text = f"""{self._create_instruction_prompt(session_info.state)}
            This is some context information about the hotel: 
            {hotel_information}
            The current date and time is {datetime.datetime.now()}."""
        msg_temp = [
                       {"role": "system", "content": system_text},
                       {"role": "assistant",
                        "content": f"Hi there! Would you like to book a hotel room? When do you arrive?"},
                   ] + messages

        missing_information = self._find_missing_info(session_info.state)
        if missing_information is not None:
            msg_temp += [{"role": "system",
                          "content": f"Do not show the booking summary yet, because there is missing information, for instance '{missing_information}'"}]

        next_response_from_bot = self.chat_gpt_adapter.chat_completion(msg_temp, None, 0.5,
                                                                       self.chat_gpt_adapter.booking_model)

        chat_control_msg = self.control_flow_manager.handle_state(session_info.state)

        if chat_control_msg.msg_to_user is not None:
            return {'text': chat_control_msg.msg_to_user, 'flag': chat_control_msg.flag}
        return {'text': next_response_from_bot.content, 'flag': None}


    def _find_missing_info(self, state: State) -> str:
        """Returns the label of any missing mandatory field"""
        missing = list(filter(lambda entry: entry.value is None and entry.mandatory,
                              state.__dict__.values()))
        return missing[0].label if len(missing) > 0 else None


    def _create_instruction_prompt(self, state: State):
        return f"""You are a hotel booking assistant. 
        Gather all information required from the user to make the booking. 
        You need to gather the following information: date of arrival, duration of stay, number of guests, 
        if they want to have breakfast included, the name of the main guest and the email address of the main guest. 
        Don't be picky regarding date formats. If you don't know the answer to a user's question say: "I don\'t know".

        At the end of the booking process you must show a booking summary.
        You must only show the booking summary after gathering all mandatory information. 
        If you don't know the date of arrival, duration of stay, number of guests, whether breakfast should be included,
        the name of the guest or the email address, do not show a booking summary!
        Use this template when showing the booking summary to the user:
        {self._create_booking_summary_msg(state)}

        Don't discuss any topics or answer questions unrelated to the hotel booking."""

    def _create_booking_summary_msg(self, state: State) -> str:
        """Creates a string summarizing the booking information"""
        price = calculate_price(state)
        price_formatted = "${:,.2f}".format(price) if price else None
        missing_information = self._find_missing_info(state)
        price_description = price_formatted if price is not None else """
        The price can not be calculated because there is missing information. 
        The date of arrival, duration of stay and number of guests is required to calculate a price"""
        return f"""<template>
        ~ Booking summary ~ 

        Date of arrival: {state.date_of_arrival.raw_value}
        Duration of stay: {state.duration_of_stay.raw_value}
        Number of guests: {state.number_of_guests.raw_value}
        Name of main guest: {state.name_of_main_guest.raw_value}
        Breakfast included?: {state.breakfast_included.raw_value}
        Email address: {state.email_address.raw_value}

        Price: {price_description}

        Check in time: after 2pm
        Check out time: before 10am

        {"Do you wish to confirm the booking?" if missing_information is None else ''}
        </template>
        {f"The total price for booking is " + price_formatted + ". You can show this value to the user, if asked for the price." if price is not None else ''}
        """
