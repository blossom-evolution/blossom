import random

def sample_stationary(organism, organism_list, world):
    return [organism]

def fast_reproduce(organism, organism_list, world):
    choice = random.randint(0, 3)
    if choice == 0 and organism.water_current > 10:
        return 'reproduce'
    elif choice == 1:
        return 'move'
    else:
        return 'drink'

def fast_actions(organism, organism_list, world):
    choice = random.randint(0, 4)
    # if choice == 0 and organism.water_current > 10 and organism.food_current > 6:
    #     return 'reproduce'
    if choice == 0:
        return 'reproduce'
    elif choice == 1:
        return 'move'
    elif choice == 2:
        return 'eat'
    else:
        return 'drink'

def try_to_live(organism, organism_list, world):
    if organism.water_current == 0:
        return 'drink'
    elif organism.food_current == 0:
        return 'eat'
    else:
        return fast_actions(organism, organism_list, world)

def move_to_live(organism, organism_list, world):
    if organism.water_current == 0:
        if world.water[organism.position[0]] > 0:
            return 'drink'
        else:
            return 'move'
    elif organism.food_current == 0:
        if world.food[organism.position[0]] > 0:
            return 'eat'
        else:
            return 'move'
    elif organism.water_current > organism.water_capacity // 2 \
            and organism.food_current > organism.food_capacity // 2:
        return 'reproduce'
    else:
        choice = random.randint(0, 3)
        if choice == 0:
            return 'move'
        elif choice == 1:
            return 'eat'
        else:
            return 'drink'
