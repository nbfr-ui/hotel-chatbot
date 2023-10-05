class StateEntry:
    def __init__(self, dim, keywords, label, mandatory=False):
        self.dim = dim
        self.keywords = keywords
        self.label = label
        self.mandatory = mandatory

    raw_value: str | None
    value: None


class State:
    def __init__(self):
        self.date_of_arrival = StateEntry('time', ['date', 'arrival'], 'Date of arrival', True)
        self.duration_of_stay = StateEntry('duration', ['duration'], 'Duration of stay', True)
        self.number_of_guests = StateEntry('number', ['number', 'guest'], 'Number of guests', True)
        self.name_of_main_guest = StateEntry('text', ['name', 'guest'], 'The name of the main guest', True)
        self.email_address = StateEntry('email', ['email'], 'Email address', True)
        self.breakfast_included = StateEntry('bool', ['breakfast'], 'Does the guest want breakfast included?', True)
        self.about_to_show_booking_summary = StateEntry('bool', ['booking summary', 'show'], '')
        self.booking_confirmed = StateEntry('bool', ['confirm'], '')
