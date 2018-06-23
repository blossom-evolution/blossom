import movement, reproduction, drinking, eating, action

class Movement():

    def move(organism, organism_list, world):
        """
        Return affected organisms
        """
        if organism.movement_type is None:
            return organism
        else:
            return getattr(movement, organism.movement_type)(organism, organism_list, world)

class Reproduction():

    def reproduce(organism, organism_list, world):
        """
        Return affected organisms
        """
        if organism.reproduction_type is None:
            return organism
        else:
            return getattr(reproduction, organism.reproduction_type)(organism, organism_list, world)

class Drinking():

    def drink(organism, organism_list, world):
        """
        Return affected organisms
        """
        if organism.drinking_type is None:
            return organism
        else:
            return getattr(drinking, organism.drinking_type)(organism, organism_list, world)

class Eating():

    def eat(organism, organism_list, world):
        """
        Return affected organisms
        """
        if organism.eating_type is None:
            return organism
        else:
            return getattr(eating, organism.eating_type)(organism, organism_list, world)

class Action():

    def act(organism, organism_list, world):
        """
        Return an action ('move', 'reproduce', 'drink', 'eat') as a string
        """
        return getattr(action, organism.action_type)(organism, organism_list, world)
