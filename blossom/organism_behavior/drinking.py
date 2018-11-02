import sys


def constant_drink(organism, organism_list, world):
    """
    Intake constant amount of water from world if water is present.
    """
    size = world.world_size

    if len(size) == 1:
        available_water = world.water[organism.position[0]]
    elif len(size) == 2:
        available_water = (world.water[organism.position[0]]
                                      [organism.position[1]])
    else:
        sys.exit('Invalid world dimensionality: %s' % len(size))

    diff = organism.water_capacity - organism.water_current
    intake = min(available_water, diff, organism.water_intake)

    organism.water_current += intake
    if len(size) == 1:
        world.water[organism.position[0]] -= intake
    else:
        world.water[organism.position[0]][organism.position[1]] -= intake

    return [organism]
