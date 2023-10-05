from datetime import datetime, time
from dateutil import parser

error_msg = {
    'Date of arrival': {'error_parsing': 'Sorry, I didn\'t unterstand. '
                                         'Could you please provide the date of your arrival?'},
    'Duration of stay': {'error_parsing': 'Could you please tell me how many nights you will stay?'},
    'Number of guests': {'error_parsing': 'Sorry, I didn\'t unterstand. How many guests will stay at our hotel?'},
    'Email address': {'error_parsing': 'Your email address is invalid. '
                                       'Could you please enter your correct email address?'}
}


class BookingInformationValidator:
    """The validator ensures that an error message is sent if a value could not be extracted or is invalid.
    E.g. foo@bla -> invalid email"""

    def has_extraction_failed(self, state: dict, key: str):
        return state[key]['raw_value'] is not None and state[key]['value'] is None

    def validate(self, state: dict) -> dict:
        for key in error_msg.keys():
            if self.has_extraction_failed(state, key):
                return {'has_error': True, 'error_msg': error_msg[key]['error_parsing']}
        if state['Date of arrival']['value'] is not None:
                parsed = parser.isoparse(state['Date of arrival']['value'])
                if parsed < datetime.combine(datetime.now(tz=parsed.tzinfo), time.min, tzinfo=parsed.tzinfo):
                    return {'has_error': True, 'error_msg': 'The booking date must not lie in the past.'}
        if state['Name of main guest']['value'] is not None:
            name = state['Name of main guest']['value']
            if len(name.split(' ')) < 2 or len(name) < 5:
                return {'has_error': True, 'error_msg': 'Please tell me your first and last name.'}
        return {'has_error': False, 'error_msg': None}
