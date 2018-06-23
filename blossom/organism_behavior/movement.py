import sys
import random

def stationary(organism, organism_list, world):
    return organism

def simple_random(organism, organism_list, world):
    new_organism = organism
    position = new_organism.position
    size = world.world_size

    if world.dimensionality == 1:
        x = position[0]
        choice = random.randint(0,2)
        if choice == 0 and x != 0:
            x -= 1
        elif choice == 1 and x != size[0]:
            x += 1
        else:
            pass
        new_organism.position = [x]
    elif world.dimensionality == 2:
        # TODO!!
        pass
    else:
        sys.exit('Invalid world dimensionality!')
    return new_organism
