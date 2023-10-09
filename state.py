class StateEntry:
    def __init__(self, dim, keywords, label, mandatory=False):
        self.dim = dim
        self.keywords = keywords
        self.label = label
        self.mandatory = mandatory
        self.value = None
        self.raw_value = None


class State:
    """Holds the most important information about the state of the conversation with the guest"""

    def __init__(self):
        self.date_of_arrival = StateEntry('time', ['date', 'arrival'], 'Date of arrival', True)
        self.duration_of_stay = StateEntry('duration', ['duration'], 'Duration of stay', True)
        self.number_of_guests = StateEntry('number', ['number', 'guest'], 'Number of guests', True)
        self.name_of_main_guest = StateEntry('text', ['name', 'guest'], 'The name of the main guest', True)
        self.email_address = StateEntry('email', ['email'], 'Email address', True)
        self.breakfast_included = StateEntry('bool', ['breakfast'], 'Does the guest want breakfast included?', True)
        self.booking_confirmed = StateEntry('bool', ['confirm'], 'Did the user confirm the booking summary?')
