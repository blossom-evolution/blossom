import copy
from organism import Organism


def hash_by_id(organism_list):
    """
    Simple hashing by organism id over a list of organisms.
    """
    hash_table = {}
    for organism in organism_list:
        id = organism.organism_id
        if id in hash_table:
            hash_table[id].append(organism)
        else:
            hash_table[id] = [organism]
    return hash_table


def hash_by_position(organism_list):
    """
    Simple hashing by organism position over a list of organisms.
    """
    hash_table = {}
    for organism in organism_list:
        position = tuple(organism.position)
        if position in hash_table:
            hash_table[position].append(organism)
        else:
            hash_table[position] = [organism]
    return hash_table


def organism_filter(organism_list, *conditions):
    """
    Selects organisms from organism list according to a set of conditions.
    Each condition should be a function that receives an Organism object as
    input and returns a boolean as output.

    Example:
    organism_filter(
        population_dict['prey1']['organisms'],
        lambda organism: (organism.alive)
    """
    remaining_list = organism_list
    for condition in conditions:
        assert callable(condition)
        remaining_list = filter(condition, remaining_list)
    return list(remaining_list)


def organism_list_copy(organism_list):
    return [organism.clone_self() for organism in organism_list]


def get_organism_list(population_dict):
    """
    Constructs organism list from population dict data structure.
    """
    organism_list = []
    for species in population_dict:
        organism_list.extend(population_dict[species]['organisms'])
    return organism_list


def get_population_dict(organism_list, species_names):
    """
    Constructs population dict from organism list data structure.
    """
    population_dict = {
        species: {
            'statistics': {
                'count': 0,
                'alive_count': 0,
                'dead_count': 0
            },
            'organisms': []
        }
        for species in species_names
    }
    for organism in organism_list:
        population_dict[organism.species_name]['organisms'].append(organism)
        population_dict[organism.species_name]['statistics']['count'] += 1
        if organism.alive:
            population_dict[organism.species_name]['statistics']['alive_count'] += 1
        else:
            population_dict[organism.species_name]['statistics']['dead_count'] += 1
    return population_dict
