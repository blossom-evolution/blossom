import sys


def constant_eat(organism, organism_list, world):
    """
    Intake constant amount of food from world if food is present.
    """
    size = world.world_size

    if len(size) == 1:
        available_food = world.food[organism.position[0]]
    elif len(size) == 2:
        available_food = (world.food[organism.position[0]]
                                    [organism.position[1]])
    else:
        sys.exit('Invalid world dimensionality: %s' % len(size))

    diff = organism.food_capacity - organism.food_current
    intake = min(available_food, diff, organism.food_intake)

    organism.food_current += intake
    if len(size) == 1:
        world.food[organism.position[0]] -= intake
    else:
        world.food[organism.position[0]][organism.position[1]] -= intake

    return [organism]
