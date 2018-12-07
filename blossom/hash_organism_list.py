def hash_by_id(organism_list):
    """
    Simple hashing by organism id over a list of organisms.
    """
    hash_table = {}
    for organism in organism_list:
        id = organism.organism_id
        if id in hash_table.keys():
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
        if position in hash_table.keys():
            hash_table[position].append(organism)
        else:
            hash_table[position] = [organism]
    return hash_table
