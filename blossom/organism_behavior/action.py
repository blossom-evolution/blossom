import random

def move_only(organism, organism_list, world):
    return 'move'

def move_and_reproduce(organism, organlism_list, world):
    choice = random.randint(0, 8)
    if choice == 0:
        return 'reproduce'
    else:
        return 'move'
