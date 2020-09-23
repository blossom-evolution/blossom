import random
import organism_list_funcs


def parse(intent_list, organism_list):
    """
    Determine whether the intent list is valid and fix it in the event of
    conflicts.

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

    Conflicts may be cases in which an organism has different states in the
    intent list, perhaps arrising from the actions of other organisms that
    somehow effect its state. This method resolves those conflicts, so that
    there is only one organism with a given organism id present in the final
    output list at all times.
    """
    # TODO: Figure out exactly how this should be controlled -- on the scale of
    # the universe, the world, or the organisms itself
    updated_list = []

    id_org_dict = dict((org.organism_id, org) for org in organism_list)
    new_organism_ids = set()

    # Randomly sample organism steps to select
    for organism_set in random.sample(intent_list, len(intent_list)):
        set_ids = set(org.organism_id for org in organism_set)
        if len(new_organism_ids & set_ids) == 0:
            updated_list.extend(organism_set)
            new_organism_ids.update(set(org.organism_id for org in organism_set))

    # Add back organisms whose steps were not chosen (and increment status)
    for id in (set(id_org_dict.keys()) - new_organism_ids):
        org = id_org_dict[id]
        if org.alive:
            updated_list.append(org.step_without_acting())

    return updated_list
