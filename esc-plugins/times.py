"""
hour_min.py - esc plugin for time operations
Copyright (c) 2023, 2026 Soren Bjornstad.

This plugin is provided with the esc distribution:
<https://github.com/sobjornstad/esc>
"""

from esc.commands import Operation, Menu, main_menu
from esc.oops import InsufficientItemsError

time_doc = """Work with quantities representing times."""
time_menu = Menu(':', 'time menu', parent=main_menu, doc=time_doc)


def sum_sixty_unit_handling(sos_hr, sos_min, bos_hr, bos_min):
    return [
         sos_hr + bos_hr,
         sos_min + bos_min,
    ]

@Operation('+', menu=time_menu, push=2,
           description='sum hr:min or min:sec',
           log_as="{0}:{1} + {2}:{3} = {4}:{5}",
           unit_handling=sum_sixty_unit_handling)
def sum_sixty(sos_hr, sos_min, bos_hr, bos_min):
    """
    Given four items, representing min:sec or hour:min quantities 1 and 2,
    sum them to another identical pair. (This works with any quantity where
    the second half operates as base-60.)
    """
    hours = sos_hr + bos_hr
    added_minutes = sos_min + bos_min
    hours += added_minutes // 60
    minutes = added_minutes % 60
    # If total time is positive, adjust hours so that minutes are expressed
    # as a positive number, and vice versa.
    while minutes < 0 and hours >= 0:
        hours -= 1
        minutes += 60
    while minutes > 0 and hours < 0:
        hours += 1
        minutes -= 60

    return hours, minutes

sum_sixty.ensure(before=[1, 0, 1, 0], after=[2, 0])
sum_sixty.ensure(before=[1, 0, 1, 30], after=[2, 30])
sum_sixty.ensure(before=[1, 30, 1, 30], after=[3, 0])
sum_sixty.ensure(before=[1, 30, 1, 35], after=[3, 5])
sum_sixty.ensure(before=[1, 30, 1, -35], after=[1, 55])
sum_sixty.ensure(before=[1, 60, 1, 5], after=[3, 5])
sum_sixty.ensure(before=[1, 80, 1, 20], after=[3, 40])
sum_sixty.ensure(before=[0, 10, -2, 50], after=[-1, 0])
sum_sixty.ensure(before=[0, 10, -2, -50], after=[-2, -40])
sum_sixty.ensure(before=[3, 5, 1], raises=InsufficientItemsError)
