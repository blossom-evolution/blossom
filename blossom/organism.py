#import organism_classes as oc
import fields
import uuid

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
        #
        # self.movement = Movement()
        # self.reproduction = Reproduction()
        # self.drinking = Drinking()
        # self.eating = Eating()

        self.intent_dict = None

    def move(self):
        pass

    def reproduce(self):
        pass

    def drink(self):
        pass

    def eat(self):
        pass

    pass

# maybe put this in species.py? depends on use in executable
def make_organism_class(movement,
                        reproduction,
                        drinking,
                        eating):
    class Organism(movement=movement,
                   reproduction=reproduction,
                   drinking=drinking,
                   eating=eating):
        pass
    return Organism

# randomization should occur at initialization
# but maybe have Universe class handle this
# MyOrganism = make_organism_class(m,r,d,e)
# organism1 = MyOrganism()
