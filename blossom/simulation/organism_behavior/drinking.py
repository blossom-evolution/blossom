def constant_drink(organism, universe):
    """
    Intake constant amount of water from world if water is present.
    """
    size = universe.world.world_size

    if len(size) == 1:
        available_water = universe.world.water[organism.location[0]]
    elif len(size) == 2:
        available_water = (universe.world.water[organism.location[0]]
                                               [organism.location[1]])
    else:
        raise ValueError(f'Invalid world dimensionality: {len(size)}')

    diff = organism.water_capacity - organism.water_current
    intake = min(available_water, diff, organism.water_intake)

    organism.water_current += intake
    if len(size) == 1:
        universe.world.water[organism.location[0]] -= intake
    else:
        universe.world.water[organism.location[0]][organism.location[1]] -= intake

    return [organism]
