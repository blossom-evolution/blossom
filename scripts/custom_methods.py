import random
import numpy as np

def sample_stationary(organism, organism_list, world):
    return [organism]

def fast_reproduce(organism, organism_list, world):
    choice = random.randint(0, 3)
    if choice == 0:
        return 'reproduce'
    elif choice == 1:
        return 'drink'
    else:
        return 'move'
