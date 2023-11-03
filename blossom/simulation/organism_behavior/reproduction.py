import uuid
import numpy as np


def pure_replication(organism, universe):
    """
    Replace organism with two organism with similar parameters.
    Essentially, only differences in parameters are organism id,
    ancestry, age, and water / food levels.
    """
    new_organism_list = []

    # Generate new organisms
    for i in range(2):
        child = organism.get_child(seed=universe.rng)
        if organism.drinking_type is not None:
            child.update_parameter('water_current',
                                   organism.water_current // 2,
                                   in_place=True)
        if organism.eating_type is not None:
            child.update_parameter('food_current',
                                   organism.food_current // 2,
                                   in_place=True)
        new_organism_list.append(child)
    new_organism_list.append(organism.die('replication'))
    return new_organism_list
