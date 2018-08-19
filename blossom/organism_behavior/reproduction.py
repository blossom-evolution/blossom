import uuid

def pure_replication(organism, organism_list, world):
    # Replace organism with two organism with similar parameters

    organism_list = []

    # Generate new organisms
    for i in range(2):
        child = organism.clone(organism)
        child.update_parameter('age', 0)
        child.update_parameter('organism_id', str(uuid.uuid4()))
        organism_list.append(child)
    return organism_list
