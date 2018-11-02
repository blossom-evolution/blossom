import sys
import random


def stationary(organism, organism_list, world):
    """
    Organism stays still.
    """
    return [organism]


def simple_random(organism, organism_list, world):
    """
    Move in random direction with equal probability. For 2D, organisms walk
    diagonally.
    """
    position = organism.position
    size = world.world_size

    if len(size) == 1:
        [x] = position
        choice = random.randint(0, 2)
        if choice == 0 and x != 0:
            x -= 1
        elif choice == 1 and x != size[0] - 1:
            x += 1
        else:
            pass
        organism.position = [x]
    elif len(size) == 2:
        [x, y] = position
        x_choice = random.randint(0, 2)
        y_choice = random.randint(0, 2)
        if x_choice == 0 and x != 0:
            x -= 1
        elif x_choice == 1 and x != size[0] - 1:
            x += 1
        else:
            pass
        if y_choice == 0 and y != 0:
            y -= 1
        elif y_choice == 1 and y != size[1] - 1:
            y += 1
        else:
            pass
        organism.position = [x, y]
    else:
        sys.exit('Invalid world dimensionality!')
    return [organism]
