"""
Common utilities used throughout :mod:`blossom`
"""

def cast_to_list(x):
    """
    Make a list out of the input if the input isn't a list.
    """
    if type(x) is list:
        return x
    else:
        return [x]
