from state import State


def calculate_price(state: State) -> str | None:
    """Returns the price for booking the hotel"""
    if state.duration_of_stay.value is None or state.number_of_guests.value is None:
        return None
    price_per_night = 100
    price_for_breakfast_per_night = 10 if state.breakfast_included.value else 0
    price = price_per_night * state.duration_of_stay.value
    price += state.number_of_guests.value * price_for_breakfast_per_night * state.duration_of_stay.value
    return "${:,.2f}".format(price)
