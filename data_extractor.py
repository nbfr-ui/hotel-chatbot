import logging
from typing import Any

from duckling_adapter import DucklingAdapter


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

    def extract_values_from_chat_bot_response(self, in_state: dict, chat_state_table: str) -> dict:
        """Extract values provided as text in form of a table into a dictionary"""
        new_state = {}
        lines = chat_state_table.split('\n')
        for key in in_state.keys():
            new_state[key] = {'dim': in_state[key]['dim'], 'keywords': in_state[key]['keywords']}
            matching_lines = list(
                filter(lambda line: all(line.lower().find(keyword) > -1 for keyword in in_state[key]['keywords']),
                       lines))
            if len(matching_lines) > 0:
                print(matching_lines[0])
                parts = matching_lines[0].split('|')
                raw_text_value = parts[2].strip() if len(parts) >= 3 else parts[1].strip()
                new_state[key]['raw_value'] = raw_text_value if (raw_text_value.lower().find(
                    'not provided') == -1 and raw_text_value.lower().find('i don\'t know') == -1) else None
                new_state[key]['value'] = self._extract_value(new_state[key]['dim'], new_state[key]['raw_value'])
            else:
                logging.warning(f"No value for key {key} found found in table data provided")
                new_state[key]['raw_value'] = None
                new_state[key]['value'] = None
        return new_state
