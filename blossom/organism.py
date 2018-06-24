import uuid

import fields
# from organism_behavior import Movement, Reproduction, Drinking, Eating, Action
from organism_behavior import movement, reproduction, drinking, eating, action

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

    def clone(self):
        return Organism(vars(self))

    def update_parameter(self, parameter, value, method='set'):
        """
        Update a specific parameter of the organism
        Args:
            parameter, string
            value
            method, string: 'set', 'add', 'subtract'

        Return:
            new Organism object with updated parameter
        """
        attribute = getattr(self, parameter)
        if method == 'set':
            attribute = value
        elif method == 'add':
            attribute += value
        elif method == 'subtract':
            attribute -= value
        else:
            sys.exit('Invalid update method!')
        setattr(self, parameter, attribute)
        return self

    def move(self, organism_list, world):
        # return Movement.move(self, organism_list, world)
        if self.movement_type is None:
            return self
        else:
            return getattr(movement, self.movement_type)(self, organism_list, world)


    def reproduce(self, organism_list, world):
        # return Reproduction.reproduce(self, organism_list, world)
        if self.reproduction_type is None:
            return self
        else:
            return getattr(reproduction, self.reproduction_type)(self, organism_list, world)


    def drink(self, organism_list, world):
        # return Drinking.drink(self, organism_list, world)
        if self.drinking_type is None:
            return self
        else:
            return getattr(drinking, self.drinking_type)(self, organism_list, world)

    def eat(self, organism_list, world):
        # return Eating.eat(self, organism_list, world)
        if self.eating_type is None:
            return self
        else:
            return getattr(eating, self.eating_type)(self, organism_list, world)

    def act(self, organism_list, world):
        """
        Call the appropriate action determined by action.act
        """
        # return getattr(Organism, Action.act(self, organism_list, world))(self, organism_list, world)
        action_name = getattr(action, self.action_type)(self, organism_list, world)
        return getattr(Organism, action_name)(self, organism_list, world)

    def living(self):
        """
        Checks whether organism is still alive
        """
        if self.age > self.max_age:
            return False
        return True

    def update_life(self, organism_list, world):
        if self.living():
            return self.update_parameter('age', 1, 'add')
        return self

    def step(self, organism_list, world):
        """
        Step through organism actions over one time unit
        """
        print(self.organism_id, self.living(), self.age)
        organism = self.clone().update_life(organism_list, world)
        if organism.living():
            return organism.act(organism_list, world)
        else:
            return organism.update_parameter('alive', False, 'set')
