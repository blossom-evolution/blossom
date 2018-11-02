import sys


def constant_drink(organism, organism_list, world):
    """
    Intake constant amount of water from world if water is present.
    """
    size = world.world_size

    if len(size) == 1:
        if world.water[organism.position[0]] > 0:
            diff = organism.water_capacity - organism.water_current
            intake = max(organism.water_intake, diff)
            organism.water_current += intake
            # for one dimension
            world.water[organism.position[0]] -= intake
    elif len(size) == 2:
        if world.water[organism.position[0]][organism.position[1]] > 0:
            diff = organism.water_capacity - organism.water_current
            intake = max(organism.water_intake, diff)
            organism.water_current += intake
            # for one dimension
            world.water[organism.position[0]][organism.position[1]] -= intake
    else:
        sys.exit('Invalid world dimensionality!')
    return [organism]
