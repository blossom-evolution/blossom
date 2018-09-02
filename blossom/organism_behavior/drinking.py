import sys
import random

def constant_drink(organism, organism_list, world):
    position = organism.position
    size = world.world_size

    if len(size) == 1:
        if world.water[organism.position[0]] > 0:

            # Actually intake water
            organism.water_current += organism.water_intake

            # for one dimension
            world.water[organism.position[0]] -= organism.water_intake

    # organism.water_current -= organism.water_metabolism
    # if organism.water_current > organism.water_capacity:
    #     organism.water_current = organism.water_capacity
    # if organism.water_current <= 0:
    #     organism.water_current = 0
    #     organism.time_without_water += 1
    # else if organism.time_without_water > 0:
    #     organism.time_without_water = 0

    return [organism]
