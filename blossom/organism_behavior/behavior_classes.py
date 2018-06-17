import movement, reproduction, drinking, eating, action

class Movement():

    def move(organism, organism_list):
        """
        Return affected organisms
        """
        if organism.movement_type is None:
            return organism
        else:
            getattr(movement, organism.movement_type)(organism, organism_list)

class Reproduction():

    def reproduce(organism, organism_list):
        """
        Return affected organisms
        """
        if organism.reproduction_type is None:
            return organism
        else:
            getattr(reproduction, organism.reproduction_type)(organism, organism_list)

class Drinking():

    def drink(organism, organism_list):
        """
        Return affected organisms
        """
        if organism.drinking_type is None:
            return organism
        else:
            getattr(drinking, organism.drinking_type)(organism, organism_list)

class Eating():

    def eat(organism, organism_list):
        """
        Return affected organisms
        """
        if organism.eating_type is None:
            return organism
        else:
            getattr(eating, organism.eating_type)(organism, organism_list)

class Action():

    def act(organism, organism_list):
        """
        Return an action ('move', 'reproduce', 'drink', 'eat') as a string
        """
        getattr(action, organism.action_type)(organism, organism_list)
