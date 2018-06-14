import uuid
import numpy as np
import fields
from organism_behavior import Movement, Reproduction, Drinking, Eating, Behavior

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

        self.movement = Movement()
        self.reproduction = Reproduction()
        self.drinking = Drinking()
        self.eating = Eating()
        self.behavior = Behavior()

    def update(self, organism):
        """
        Update organism dict with parameters from organism
        """
        pass

    def move(self, organism_list):
        return movement.move(self, organism_list)

    def reproduce(self, organism_list):
        return reproduction.reproduce(self, organism_list)

    def drink(self, organism_list):
        return drinking.drink(self, organism_list)

    def eat(self, organism_list):
        return eating.eat(self, organism_list)

    def act(self, organism_list):
        """
        Call the appropriate action determined by behavior.act
        """
        return globals()[behavior.act(self, organism_list)](self, organism_list)
        # a = np.random.randint(0,5)
        # if a == 0:
        #     return move(self, organism_list)
        # elif a == 1:
        #     return reproduce(self, organism_list)
        # elif a == 2:
        #     return drink(self, organism_list)
        # elif a == 3:
        #     return eat(self, organism_list)
        # else:
        #     return self
