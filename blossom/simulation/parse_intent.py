import random
from . import population_funcs


def parse(intent_list, organism_list):
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
    # TODO: Figure out exactly how this should be controlled -- on the scale of
    # the universe, the world, or the organisms itself
    updated_list = []

    id_org_dict = {}
    for organism in organism_list:
        id_org_dict[organism.organism_id] = organism

    new_organism_ids = set()

    # Randomly sample organism steps to select. Only use sets for conditionals,
    # add to saved structures using lists and dicts (since key order is
    # preserved)
    for organism_set in random.sample(intent_list, len(intent_list)):
        set_ids = set(organism.organism_id for organism in organism_set)
        if len(new_organism_ids & set_ids) == 0:
            updated_list.extend(organism_set)
            new_organism_ids.update(set_ids)

    # Add back organisms whose steps were not chosen (and increment status)
    for id in id_org_dict.keys():
        if id not in new_organism_ids:
            organism = id_org_dict[id]
            if organism.alive:
                updated_list.append(organism.step_without_acting())

    return updated_list
