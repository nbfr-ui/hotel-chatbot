import logging
from typing import Any

from duckling_adapter import DucklingAdapter
from state import State


class DataExtractor:
    """This class uses duckling to extract / parse information given in text form to the respective data types"""
    duckling_adapter = DucklingAdapter()

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

    def extract_values_from_chat_bot_response(self, chat_state_table: str) -> State:
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
