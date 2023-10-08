from datetime import datetime, time

from dateutil import parser

from state import State, StateEntry

error_msg = {
    'date_of_arrival': {'error_parsing': 'Sorry, I didn\'t unterstand. '
                                         'Could you please provide the date of your arrival?'},
    'duration_of_stay': {'error_parsing': 'Could you please tell me how many nights you will stay?'},
    'number_of_guests': {'error_parsing': 'Sorry, I didn\'t unterstand. How many guests will stay at our hotel?'},
    'email_address': {'error_parsing': 'Your email address is invalid. '
                                       'Could you please enter your correct email address?'}
}


class BookingInformationValidator:
    """The validator ensures that an error message is sent if a value could not be extracted or is invalid.
    E.g. foo@bla -> invalid email"""

    def has_extraction_failed(self, state_entry: StateEntry):
        return state_entry.raw_value is not None and state_entry.value is None

    def validate(self, state: State) -> dict:
        for attribute, entry in state.__dict__.items():
            if attribute in error_msg and self.has_extraction_failed(entry):
                return {'has_error': True, 'error_msg': error_msg[attribute]['error_parsing']}
        if state.date_of_arrival.value is not None:
            parsed = parser.isoparse(state.date_of_arrival.value)
            if parsed < datetime.combine(datetime.now(tz=parsed.tzinfo), time.min, tzinfo=parsed.tzinfo):
                return {'has_error': True, 'error_msg': 'The booking date must not lie in the past.'}
        if state.name_of_main_guest.value is not None:
            name = state.name_of_main_guest.value
            if len(name.split(' ')) < 2 or len(name) < 5:
                return {'has_error': True, 'error_msg': 'Please tell me your first and last name.'}
        if state.number_of_guests.value is not None and float(int(state.number_of_guests.value)) != float(
                state.number_of_guests.value):
            return {'has_error': True, 'error_msg': 'The number of guests must be a whole number.'}
        if state.duration_of_stay.value is not None and float(int(state.duration_of_stay.value)) != float(
                state.duration_of_stay.value):
            return {'has_error': True, 'error_msg': 'The duration of stay must be a whole number of nights.'}
        return {'has_error': False, 'error_msg': None}
