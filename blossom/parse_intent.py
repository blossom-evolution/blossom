import os
import glob
import json
import random

import default_fields
from world import World
from organism import Organism
import hash_organism_list


def parse(intent_list, organism_list):
    """
    Determine whether the intent list is valid and fix it otherwise.

    Parameters
    ----------
    intent_list : list of Organisms
        List of organisms with proposed organism states,
        after each organism has 'acted'
    organism_list : list of Organisms
        List of current organisms

    Returns
    -------
    updated_list : list of Organisms
        List of updated organisms with conflicts between intent_list and
        organism_list resolved.
    """
    # TODO: Figure out exactly how this should be controlled -- on the scale of
    # the universe, the world, or the organisms itself
    updated_list = []
    id_hash_table = hash_organism_list.hash_by_id(intent_list)
    for id in id_hash_table.keys():
        if len(id_hash_table[id]) == 1:
            updated_list.extend(id_hash_table[id])
        else:
            selected = False
            for organism in id_hash_table[id]:
                # If organism died in this timestep, add it to the list.
                if organism.age_at_death == organism.age:
                    updated_list.append(organism)
                    selected = True
                    break
            if not selected:
                # If no organism died, then find first available organism.
                # For more complicated circumstances, this may need to be
                # extended.
                updated_list.append(id_hash_table[id][0])
    return updated_list
