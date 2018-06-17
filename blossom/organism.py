import uuid
import numpy as np
import fields
from organism_behavior import Movement, Reproduction, Drinking, Eating, Action

class Organism(object):
    """ Create a base organism structure for all species """

    def __init__(self, init_dict = {}):
        """ Create a new organism with arguments based on the species
            parameter files """

        # Sets up defaults based on species parameters
        for (prop, default) in fields.species_field_names.items():
            setattr(self, prop, init_dict.get(prop, default))

        # Sets up defaults based on organism parameters
        for (prop, default) in fields.specific_organism_field_names.items():
            setattr(self, prop, init_dict.get(prop, default))

    def move(self, organism_list):
        return Movement.move(self, organism_list)

    def reproduce(self, organism_list):
        return Reproduction.reproduce(self, organism_list)

    def drink(self, organism_list):
        return Drinking.drink(self, organism_list)

    def eat(self, organism_list):
        return Eating.eat(self, organism_list)

    def act(self, organism_list):
        """
        Call the appropriate action determined by action.act
        """
        return globals()[Action.act(self, organism_list)](self, organism_list)
