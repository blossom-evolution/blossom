import movement, reproduction, drinking, eating, action

class Movement(object):

    def move(organism, organism_list):
        """
        Return affected organisms
        """
        getattr(movement, organism.movement_type)(organism, organism_list)

class Reproduction(object):

    def reproduce(organism, organism_list):
        """
        Return affected organisms
        """
        getattr(reproduction, organism.reproduction_type)(organism, organism_list)

class Drinking(object):

    def drink(organism, organism_list):
        """
        Return affected organisms
        """
        getattr(drinking, organism.drinking_type)(organism, organism_list)

class Eating(object):

    def eat(organism, organism_list):
        """
        Return affected organisms
        """
        getattr(eating, organism.eating_type)(organism, organism_list)

class Action(object):

    def act(organism, organism_list):
        """
        Return an action ('move', 'reproduce', 'drink', 'eat') as a string
        """
        getattr(action, organism.action_type)(organism, organism_list)
