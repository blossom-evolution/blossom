"""
Common utilities used throughout :mod:`blossom`
"""

import math


def cast_to_list(x):
    """
    Make a list out of the input if the input isn't a list.
    """
    if type(x) is list:
        return x
    else:
        return [x]


def time_to_string(seconds):
    """
    Convert time in seconds to the most reasonable representation.
    """
    if seconds < 1:
        return '%1.3f s' % seconds
    elif seconds < 60:
        return '%.2f s' % seconds
    elif seconds < 3600:
        minutes = math.floor(seconds / 60)
        seconds -= minutes * 60
        return '%d m %04.1f s' % (minutes, seconds)
    else:
        hours = math.floor(seconds / 3600)
        seconds -= hours * 3600
        minutes = math.floor(seconds / 60)
        seconds -= minutes * 60
        return '%d h %02d m %02d s' % (hours, minutes, seconds)
