def move_only(organism, universe):
    """
    Only move.
    """
    return 'move'


def move_and_reproduce(organism, universe):
    """
    Move and reproduce. Reproduction occurs with probability 1/8.
    """
    return universe.rng.choice(['reproduce', 'move'], 
                               p=[1/8, 7/8])


def move_and_drink(organism, universe):
    """
    Move and drink. Each occurs with probability 1/2.
    """
    return universe.rng.choice(['drink', 'move'])


def move_reproduce_drink(organism, universe):
    """
    Move, drink, and reproduce. Reproduction occurs with probability 1/8.
    Drinks with probability 3/8, and moves with probability 1/2.
    """
    return universe.rng.choice(['reproduce', 'drink', 'move'], 
                               p=[1/8, 3/8, 1/2])
