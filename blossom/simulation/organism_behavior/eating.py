def constant_eat(organism, universe):
    """
    Intake constant amount of food from world if food is present.
    """
    size = universe.world.world_size

    if len(size) == 1:
        available_food = universe.world.food[organism.location[0]]
    elif len(size) == 2:
        available_food = (universe.world.food[organism.location[0]]
                                             [organism.location[1]])
    else:
        raise ValueError(f'Invalid world dimensionality: {len(size)}')

    diff = organism.food_capacity - organism.food_current
    intake = min(available_food, diff, organism.food_intake)

    organism.food_current += intake
    if len(size) == 1:
        universe.world.food[organism.location[0]] -= intake
    else:
        universe.world.food[organism.location[0]][organism.location[1]] -= intake

    return [organism]
