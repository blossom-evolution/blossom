import uuid

import fields
from organism_behavior import Movement, Reproduction, Drinking, Eating, Action

class Organism(object):
    """ Create a base organism structure for all species """

    def __init__(self, init_dict = {}):
        """ Create a new organism with arguments based on the species
            parameter files """

        # Sets up defaults based on organism parameters
        for (prop, default) in fields.organism_field_names.items():
            setattr(self, prop, init_dict.get(prop, default))

        # Set unique id
        if self.organism_id is None:
            self.organism_id = str(uuid.uuid4())

    def move(self, organism_list, world):
        return Movement.move(self, organism_list, world)

    def reproduce(self, organism_list, world):
        return Reproduction.reproduce(self, organism_list, world)

    def drink(self, organism_list, world):
        return Drinking.drink(self, organism_list, world)

    def eat(self, organism_list, world):
        return Eating.eat(self, organism_list, world)

    def act(self, organism_list, world):
        """
        Call the appropriate action determined by action.act
        """
        return globals()[Action.act(self, organism_list, world)](self, organism_list, world)
