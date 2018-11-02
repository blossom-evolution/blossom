import uuid
import math


def pure_replication(organism, organism_list, world):
    """
    Replace organism with two organism with similar parameters.
    Essentially, only differences in parameters are organism id,
    ancestry, age, and water / food levels.
    """

    new_organism_list = []

    # Generate new organisms
    for i in range(2):
        child = organism.clone(organism)
        child.update_parameter('age', 0)
        child.update_parameter('organism_id', str(uuid.uuid4()))
        child.update_parameter('ancestry', organism.organism_id, 'append')
        if organism.drinking_type is not None:
            child.update_parameter('water_current',
                                   math.floor(organism.water_current / 2))
        if organism.eating_type is not None:
            child.update_parameter('food_current',
                                   math.floor(organism.food_current / 2))
        new_organism_list.append(child)
    return new_organism_list
