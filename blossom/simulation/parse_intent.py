import random
import numpy as np
from . import population_funcs


def parse(intent_list, organism_list, seed=None):
    """
    Determine whether the intent list is valid and fix it in the event of
    conflicts.

    Parameters
    ----------
    intent_list : list of lists of Organisms
        List of lists of organisms with proposed organism states,
        after each organism has 'acted'. Length equals number of organisms in
        the current time step.
    organism_list : list of Organisms
        List of current organisms
    seed : int, Generator, optional
        Random seed 

    Returns
    -------
    updated_organism_list : list of Organisms
        List of updated organisms, where organism states that conflict between
        ``intent_list`` and ``organism_list`` are resolved.

    Conflicts may be cases in which an organism has different states in the
    intent list, perhaps arrising from the actions of other organisms that
    somehow effect its state. This method resolves those conflicts, so that
    there is only one organism with a given organism id present in the final
    output list at all times.
    """
    rng = np.random.default_rng(seed)
    # TODO: Figure out exactly how this should be controlled -- on the scale of
    # the universe, the world, or the organisms itself
    updated_list = []
    id_org_dict = {
        organism.organism_id: organism
        for organism in organism_list
    }

    new_organism_ids = set()

    # Randomly sample organism steps to select. Only use sets for conditionals,
    # add to saved structures using lists and dicts (since key order is
    # preserved)
    rng.shuffle(intent_list)
    for organism_set in intent_list:
        set_ids = {organism.organism_id for organism in organism_set}
        if new_organism_ids.isdisjoint(set_ids):
            updated_list.extend(organism_set)
            new_organism_ids.update(set_ids)

    # Add back organisms whose steps were not chosen (and increment status)
    for organism_id, organism in id_org_dict.items():
        if organism_id not in new_organism_ids:
            if organism.alive:
                updated_list.append(organism.step_without_acting())

    return updated_list
