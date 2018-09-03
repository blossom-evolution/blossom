import random

def move_only(organism, organism_list, world):
    return 'move'

def move_and_reproduce(organism, organism_list, world):
    choice = random.randint(0, 8)
    if choice == 0:
        return 'reproduce'
    else:
        return 'move'

def move_and_drink(organism, organism_list, world):
    choice = random.randint(0, 8)
    if choice < 4:
        return 'drink'
    else:
        return 'move'

def move_reproduce_drink(organism, organism_list, world):
    choice = random.randint(0, 8)
    if choice == 0:
        return 'reproduce'
    elif choice < 4:
        return 'drink'
    else:
        return 'move'
