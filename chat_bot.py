import datetime
import json
import logging

from chat_gpt_adapter import ChatGptAdapter
from control_flow_manager import ControlFlowManager
from price_calculator import calculate_price
from session_info import SessionInfo
from state import State

# this text is used to describe the task to the chatbot
task_description = """You are a hotel booking assistant. 
Gather all information required from the user to make the booking. 
You need to gather the following information: date of arrival, duration of stay, number of guests, 
if they want to have breakfast included, the name of the main guest and the email address of the main guest. 
Don't be picky regarding date formats. If you don't know the answer to a user's question say: "I don\'t know".
At the end of the booking process you MUST show a booking summary with all booking information 
and ask the user to confirm the booking."""

# this text provides context information about to hotel
hotel_information = """Name of the hotel: Hotel Royal
Address: Main square, Madrid, Spain
Check in time: 2pm, check out time: 10am.
Room sized: the hotel offers double bed standard rooms exclusively. The maximal number of guests for such a room is 3.
Breakfast: $10 per guest per night. The breakfast offers several juices, bread, coffee and boiled eggs.
Facilities: a small gym and sauna.
Animals are not allowed.
Price per night: about $100. A accurate price will be given at the end of the booking process."""


class ChatBot:
    """The main interface of the chatbot."""

    control_flow_manager = ControlFlowManager()
    chat_gpt_adapter = ChatGptAdapter()

    def get_price_of_booking(self, state: State):
        """Calculates the price for the booking and returns a ChatGPT function response"""
        price = calculate_price(state)
        info = {
            "total_price": price if price is not None else """The price can not be calculated because there is missing 
            information. The date of arrival, duration of stay and number of guests is required to calculate a price""",
            "unit": '$',
        }
        return json.dumps(info)

    functions = [
        {
            "name": "get_price_for_booking",
            "description": "Calculates the price in USD for booking the hotel room",
            "parameters": {
                "type": "object",
                "properties": {
                    "price_per_night_without_breakfast": {
                        "type": "number",
                        "description": "The price per night for a hotel room, breakfast excluded",
                    },
                    "total_price": {
                        "type": "number",
                        "description": "The total price for booking the hotel room",
                    }
                },
                "required": [],
            },
        }
    ]

    def continue_chat(
            self,
            session_info: SessionInfo,
            messages: list,
    ) -> dict:
        """This method receives the chat history and generates a chat response"""
        logging.info(f"Enter continue_chat")

        system_text = f"""{task_description}
            This is some context information about the hotel: 
            {hotel_information}
            The current date and time is {datetime.datetime.now()}."""
        msg_temp = [
                       {"role": "system", "content": system_text},
                       {"role": "assistant",
                        "content": f"Hi there! Would you like to book a hotel room? When do you arrive?"},
                   ] + messages

        next_response_from_bot = self.chat_gpt_adapter.chat_completion(msg_temp, self.functions, 0.5,
                                                                       self.chat_gpt_adapter.booking_model)

        if "function_call" in next_response_from_bot:
            session_info.state = self.control_flow_manager.extract_state(messages, next_response_from_bot.content,
                                                                         self.chat_gpt_adapter)
            msg_temp.append(next_response_from_bot)
            msg_temp.append(
                {
                    "role": "function",
                    "name": "get_price_for_booking",
                    "content": self.get_price_of_booking(session_info.state),
                }
            )
            next_response_from_bot = self.chat_gpt_adapter.chat_completion(msg_temp, None, 0.5,
                                                                           self.chat_gpt_adapter.booking_model)
        session_info.state = self.control_flow_manager.extract_state(messages, next_response_from_bot.content,
                                                                     self.chat_gpt_adapter)
        chat_control_msg = self.control_flow_manager.handle_state(session_info.state)

        if chat_control_msg.msg_to_user is not None:
            return {'text': chat_control_msg.msg_to_user, 'flag': chat_control_msg.flag}
        elif chat_control_msg.msg_to_bot is not None:
            msg_temp = messages + [{"role": "user", "content": chat_control_msg.msg_to_bot}]
            return {'text': self.chat_gpt_adapter.chat_completion(msg_temp, self.functions).content, 'flag': None}
        return {'text': next_response_from_bot.content, 'flag': None}
