import sys
import random

def constant_eat(organism, organism_list, world):
    """
    Intake constant amount of food from world if food is present.
    """
    size = world.world_size

    if len(size) == 1:
        if world.food[organism.position[0]] > 0:
            diff = organism.food_capacity - organism.food_current
            intake = max(organism.food_intake, diff)
            organism.food_current += intake
            # for one dimension
            world.food[organism.position[0]] -= intake

    return [organism]
