"""
trig.py - esc plugin for trigonometric functions
Copyright (c) 2019 Soren Bjornstad.

This plugin is provided with the esc distribution:
<https://github.com/sobjornstad/esc>
"""
import math

from esc import modes
from esc.commands import Menu, Function, Mode, ModeChange, UNOP, main_menu

TRIG_MODE_NAME = 'trig_mode'

trig_doc = """
    Calculate the values of trigonometric functions, treating inputs as
    either degrees or radians depending on the mode.
"""


def trig_mode_display():
    return f"[{modes.get(TRIG_MODE_NAME)}]"


trig_menu = Menu('t',
                 'trig menu',
                 parent=main_menu,
                 doc=trig_doc,
                 mode_display=trig_mode_display)


def trig_wrapper(bos, func, arc=False):
    """
    Used anytime a trig Function is called. Performs any conversions from
    degrees to radians and vice versa, as called for by modes.trigMode (all
    Python math module functions use only radians).

    Takes the requested stack item, a Function to be called on the value
    after/before the appropriate conversion, and a boolean indicating whether
    this is an arc/inverse Function (requiring radian->degree after
    computation) or a forward one (requiring degree->radian before
    computation).

    Returns the new value of the stack as passed out by the provided Function,
    after possible conversion to degrees.
    """
    if modes.get(TRIG_MODE_NAME) == 'degrees' and not arc:
        bos = math.radians(bos)
    ret = func(bos)
    if modes.get(TRIG_MODE_NAME) == 'degrees' and arc:
        ret = math.degrees(ret)
    return ret


@Function('s', menu=trig_menu, push=1, description='sine', log_as=UNOP)
def sine(bos):
    """
    Take the sine of bos. Affected by the mode 'degrees' or 'radians'
    shown in the trig menu.
    """
    return trig_wrapper(bos, math.sin)


@Function('c', menu=trig_menu, push=1, description='cosine', log_as=UNOP)
def cosine(bos):
    """
    Take the cosine of bos. Affected by the mode 'degrees' or 'radians'
    shown in the trig menu.
    """
    return trig_wrapper(bos, math.cos)


@Function('t', menu=trig_menu, push=1, description='tangent', log_as=UNOP)
def tangent(bos):
    """
    Take the tangent of bos. Affected by the mode 'degrees' or 'radians'
    shown in the trig menu.
    """
    return trig_wrapper(bos, math.tan)


@Function('i', menu=trig_menu, push=1, description='arc sin', log_as=UNOP)
def arc_sine(bos):
    """
    Take the arc sine (a.k.a., inverse sine) of bos. Affected by the mode
    'degrees' or 'radians' shown in the trig menu.
    """
    return trig_wrapper(bos, math.sin)


@Function('o', menu=trig_menu, push=1, description='arc cos', log_as=UNOP)
def arc_cosine(bos):
    """
    Take the arc cosine (a.k.a., inverse cosine) of bos. Affected by the mode
    'degrees' or 'radians' shown in the trig menu.
    """
    return trig_wrapper(bos, math.cos)


@Function('a', menu=trig_menu, push=1, description='arc tan', log_as=UNOP)
def arc_tangent(bos):
    """
    Take the arc cosine (a.k.a., inverse cosine) of bos. Affected by the mode
    'degrees' or 'radians' shown in the trig menu.
    """
    return trig_wrapper(bos, math.tan)


Mode(name=TRIG_MODE_NAME,
     default_value='radians',
     allowable_values=('degrees', 'radians'))
ModeChange(key='d',
           description='degrees',
           menu=trig_menu,
           mode_name=TRIG_MODE_NAME,
           to_value='degrees')
ModeChange(key='r',
           description='radians',
           menu=trig_menu,
           mode_name=TRIG_MODE_NAME,
           to_value='radians')
