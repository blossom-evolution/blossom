def stationary(organism, universe):
    """
    Organism stays still.
    """
    return [organism]


def simple_random(organism, universe):
    """
    Move in random direction with equal probability. For 2D, organisms walk
    diagonally.
    """
    location = organism.location
    size = universe.world.world_size

    if len(size) == 1:
        [x] = location

        choice = universe.rng.choice([-1, 1])
        x += choice 
        if x == -1:
            x = 0
        elif x == size[0]:
            x = size[0] - 1
            
        organism.location = [x]
    elif len(size) == 2:
        [x, y] = location

        x_choice = universe.rng.choice([-1, 1])
        x += x_choice 
        if x == -1:
            x = 0
        elif x == size[0]:
            x = size[0] - 1

        y_choice = universe.rng.choice([-1, 1])
        y += y_choice 
        if y == -1:
            y = 0
        elif y == size[1]:
            y = size[1] - 1
            
        organism.location = [x, y]
    else:
        raise ValueError(f'Invalid world dimensionality: {len(size)}')
    return [organism]
