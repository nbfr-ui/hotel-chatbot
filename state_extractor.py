import json
import logging
from typing import Any

from chat_gpt_adapter import ChatGptAdapter
from duckling_adapter import DucklingAdapter
from state import State


class StateExtractor:
    """This class queries chatGPT and uses duckling to extract / parse to the respective data types"""
    duckling_adapter = DucklingAdapter()

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

    def query_state(self, messages: list, chat_gpt_adapter: ChatGptAdapter) -> State:
        """Returns a state object given the chat history"""
        chat_state_table = self._query_chat_state_from_bot(messages, chat_gpt_adapter)
        return self._extract_values_from_chat_bot_response(chat_state_table)

    def _query_chat_state_from_bot(self, messages: list, adapter: ChatGptAdapter) -> str:
        """Queries information about the chat history and last chat message from ChatGPT."""
        logging.info('Enter _query_chat_state_from_bot')
        copy_of_chat = messages.copy()
        copy_of_chat.append(
            {"role": "user", "content": self.structured_data_query})

        booking_info_table = adapter.chat_completion(copy_of_chat, 0.2, adapter.structured_query_model).content
        logging.debug("Response to state query: " + json.dumps(copy_of_chat + [{"role": "assistant", "content": booking_info_table}]))

        return booking_info_table

    def _extract_values_from_chat_bot_response(self, chat_state_table: str) -> State:
        """Extract values provided as text in form of a table into a State object"""
        new_state = State()
        lines = chat_state_table.split('\n')
        for attribute, entry in new_state.__dict__.items():
            matching_lines = list(
                filter(lambda line: all(line.lower().find(keyword) > -1 for keyword in entry.keywords),
                       lines))
            if len(matching_lines) > 0:
                parts = matching_lines[0].split('|')
                raw_text_value = parts[2].strip() if len(parts) >= 3 else parts[1].strip()
                entry.raw_value = raw_text_value if (raw_text_value.lower().find(
                    'not provided') == -1 and raw_text_value.lower().find('i don\'t know') == -1) else None
                entry.value = self._extract_value(entry.dim, entry.raw_value)
            else:
                logging.warning(f"No value for key {attribute} found found in table data provided")
                entry.raw_value = None
                entry.value = None
        return new_state

    def _extract_value(self, dim: str, value: str | None) -> Any:
        if value is None:
            return None
        match dim:
            case 'bool':
                return value.lower().find('yes') > -1
            case 'number' | 'time' | 'duration' | 'email':
                extracted_value = self.duckling_adapter.query_duckling(value, dim)
                # fall back if there is no duration but just a number e.g. '2 nights'
                if extracted_value is None and dim == 'duration':
                    extracted_value = self.duckling_adapter.query_duckling(value, 'number')
                return extracted_value
            case _:
                return value
