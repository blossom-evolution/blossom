import uuid
import math


def pure_replication(organism, organism_list, world, position_hash_table=None):
    """
    Replace organism with two organism with similar parameters.
    Essentially, only differences in parameters are organism id,
    ancestry, age, and water / food levels.
    """

    new_organism_list = []

    # Generate new organisms
    for i in range(2):
        child = organism.clone_self()
        child.update_parameter('age', 0, in_place=True)
        child.update_parameter('organism_id', str(uuid.uuid4()), in_place=True)
        child.update_parameter('ancestry', organism.organism_id, 'append', in_place=True)
        child.update_parameter('last_action', None, in_place=True)
        if organism.drinking_type is not None:
            child.update_parameter('water_current',
                                   math.floor(organism.water_current / 2),
                                   in_place=True)
        if organism.eating_type is not None:
            child.update_parameter('food_current',
                                   math.floor(organism.food_current / 2),
                                   in_place=True)
        new_organism_list.append(child)
    new_organism_list.append(organism.die('replication'))
    return new_organism_list
