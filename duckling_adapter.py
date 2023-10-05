import logging
from typing import Any
import requests


class DucklingAdapter:
    """This class communicates with the ducking docker container on port 8000 to extract information from text"""
    def query_duckling(
            self,
            text: str,
            dimension: str
    ) -> Any:
        try:
            response = requests.post('http://0.0.0.0:8000/parse', data={"text": text, "dims": f'["{dimension}"]' }).json()
            if len(response) > 0:
                if 'normalized' in response[0]['value'] and dimension == 'duration':
                    return response[0]['value']['normalized']['value'] / 24 / 3600
                if 'value' in response[0]['value']:
                    return response[0]['value']['value']
                elif 'values' in response[0]['value']:
                    return response[0]['value']['values'][0]
            return None
        except Exception as e:
            logging.error(e)
