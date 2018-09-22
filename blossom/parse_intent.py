import os
import glob
import json
import random

import fields
from world import World
from organism import Organism

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
    for organism in intent_list:
        if organism.age_at_death is None or organism.age_at_death == organism.age:
            updated_list.append(organism)
    return updated_list
