import datetime
import logging

from chat_gpt_adapter import ChatGptAdapter
from control_flow_manager import ControlFlowManager

# this text is used to describe the task to the chatbot
task_description = """You are a hotel booking assistant. 
Gather all information required from the user to make the booking. 
You need to gather the following information: date of arrival, duration of stay, number of guests, 
if they want to have breakfast included, the name of the main guest and the email address of the main guest. 
Don't be picky regarding date formats. If you don't know the answer to a question say: 'I don\"t know'.
At the end of the booking process you MUST show a booking summary with all booking information 
and ask the user to confirm the booking."""

# this text provides context information about to hotel
hotel_information = """Name of the hotel: Hotel Royal
Address: Main square, Madrid, Spain
Check in time: 2pm, check out time: 10am.
Room sized: the hotel offers double bed standard rooms exclusively. The maximal number of guests for such a room is 3.
Breakfast: $10 per guest per night.
Facilities: a small gym and sauna.
Price per night: about $100. A accurate price will be given at the end of the booking process."""


class ChatBot:
    """The main interface of the chatbot."""

    control_flow_manager = ControlFlowManager()
    chat_gpt_adapter = ChatGptAdapter()

    def continue_chat(
            self,
            messages: list
    ) -> dict:
        """This method receives the chat history and a session info and generates a chat response"""
        logging.info(f"Enter continue_chat")
        last_message = messages[-1]

        if len(last_message["content"]) > 400:
            return {'text': "Your message is too long. Please provide a shorter text", 'flag': None}

        system_text = f"""{task_description}
            This is some context information about the hotel: 
            {hotel_information}
            The current date and time is {datetime.datetime.now()}."""
        msg_temp = [
                       {"role": "system", "content": system_text},
                       {"role": "assistant",
                        "content": f"Hi there! Would you like to book a hotel room? When do you arrive?"},
                   ] + messages
        next_response_from_bot = self.chat_gpt_adapter.chat_completion(msg_temp)

        chat_control_msg = self.control_flow_manager.handle_state(messages, next_response_from_bot,
                                                                  self.chat_gpt_adapter)

        if chat_control_msg['msg_to_user'] is not None:
            return {'text': chat_control_msg['msg_to_user'], 'flag': chat_control_msg['flag']}
        elif chat_control_msg['msg_to_bot'] is not None:
            messages += [{"role": "system", "content": chat_control_msg['msg_to_bot']}]
            return self.continue_chat(messages)
        return {'text': next_response_from_bot, 'flag': None}
