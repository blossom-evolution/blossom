import uuid
import copy
import imp
import sys

import fields
from organism_behavior import movement, reproduction, drinking, eating, action

def cast_to_list(x):
    if type(x) is list:
        return x
    else:
        return [x]

class Organism(object):
    """ Create a base organism structure for all species """

    def __init__(self, init_dict = {}):
        """ Create a new organism with arguments based on the species
            parameter files """

        # Sets up defaults based on organism parameters
        for (prop, default) in fields.organism_field_names.items():
            setattr(self, prop, init_dict.get(prop, default))

        # Set unique id for organism
        if self.organism_id is None:
            self.organism_id = str(uuid.uuid4())

        if self.drinking_type is not None and self.water_current is None:
            self.water_current = self.water_initial

        if self.eating_type is not None and self.food_current is None:
            self.food_current = self.food_initial

        # Import custom modules / paths
        if self.custom_methods_fns is not None:
            self.custom_modules = []
            for i, path in enumerate(cast_to_list(self.custom_methods_fns)):
                temp_module = imp.load_source('%s' % i, path)
                self.custom_modules.append(temp_module)


    @classmethod
    def clone(cls, organism):
        """
        Makes a new Organism object identical to the current one.
        """
        new_organism = cls(vars(organism))
        # Use copy module to properly handle mutable lists
        new_organism.ancestry = copy.copy(new_organism.ancestry)
        new_organism.position = copy.copy(new_organism.position)
        return new_organism

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
        elif method == 'append':
            attribute.append(value)
        else:
            sys.exit('Invalid update method!')
        setattr(self, parameter, attribute)
        return self

    def move(self, organism_list, world):
        # return Movement.move(self, organism_list, world)
        if self.movement_type is None:
            sys.exit('No movement type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.movement_type):
                    return getattr(custom_module, self.movement_type)(self, organism_list, world)
        return getattr(movement, self.movement_type)(self, organism_list, world)

    def reproduce(self, organism_list, world):
        # return Reproduction.reproduce(self, organism_list, world)
        if self.reproduction_type is None:
            sys.exit('No reproduction type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.reproduction_type):
                    return getattr(custom_module, self.reproduction_type)(self, organism_list, world)
        return getattr(reproduction, self.reproduction_type)(self, organism_list, world)

    def drink(self, organism_list, world):
        # return Drinking.drink(self, organism_list, world)
        if self.drinking_type is None:
            sys.exit('No drinking type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.drinking_type):
                    return getattr(custom_module, self.drinking_type)(self, organism_list, world)
        return getattr(drinking, self.drinking_type)(self, organism_list, world)

    def eat(self, organism_list, world):
        # return Eating.eat(self, organism_list, world)
        if self.eating_type is None:
            sys.exit('No eating type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.eating_type):
                    return getattr(custom_module, self.eating_type)(self, organism_list, world)
        return getattr(eating, self.eating_type)(self, organism_list, world)

    def act(self, organism_list, world):
        """
        Call the appropriate action determined by action.act
        """
        # return getattr(Organism, Action.act(self, organism_list, world))(self, organism_list, world)
        action_name = None
        if self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.action_type):
                    action_name = getattr(custom_module, self.action_type)(self, organism_list, world)
        if action_name is None:
            action_name = getattr(action, self.action_type)(self, organism_list, world)
        return cast_to_list(getattr(self, action_name)(organism_list, world))

    def update_age(self, organism_list, world):
        return self.update_parameter('age', 1, 'add')

    def update_water(self, organism_list, world):
        self.water_current -= self.water_metabolism

        if self.water_current > self.water_capacity:
            self.water_current = self.water_capacity
        elif self.water_current <= 0:
            self.water_current = 0
            self.time_without_water += 1
        elif self.time_without_water > 0:
            self.time_without_water = 0
        return self

    def update_food(self, organism_list, world):
        self.food_current -= self.food_metabolism

        if self.food_current > self.food_capacity:
            self.food_current = self.food_capacity
        elif self.food_current <= 0:
            self.food_current = 0
            self.time_without_food += 1
        elif self.time_without_food > 0:
            self.time_without_food = 0
        return self

    def at_death(self, cause):
        """Check various conditions for death"""
        if cause == 'old_age':
            return self.age > self.max_age
        elif cause == 'thirst':
            return self.drinking_type is not None and self.time_without_water > self.max_time_without_water
        elif cause == 'hunger':
            return self.eating_type is not None and self.time_without_food > self.max_time_without_food
        else:
            sys.exit('Invalid cause!')

    def die(self, cause):
        # cause is string describing cause of death
        self.update_parameter('alive', False)
        self.update_parameter('age_at_death', self.age)
        self.update_parameter('cause_of_death', cause)
        return self

    def step(self, organism_list, world):
        """
        Step through organism actions over one time unit.

        Returns a list of organisms that the action produced (either new or
        altered organisms)
        """
        # Create new Organism object / reference and update age
        organism = self.clone(self).update_age(organism_list, world)
        if organism.alive:
            if not organism.at_death('old_age'):
                # Keep acting if alive
                affected_organisms = organism.act(organism_list, world)
                for org in affected_organisms:
                    if org.drinking_type is not None:
                        org.update_water(organism_list, world)
                        if org.at_death('thirst'):
                            org.die('thirst')
                    if org.eating_type is not None:
                        org.update_food(organism_list, world)
                        if org.at_death('hunger'):
                            org.die('hunger')
                return affected_organisms
            else:
                # Here, organism is at death from old age
                return [organism.die('old_age')]
        else:
            # Organism status already set to dead, so return organism
            # (with 'age' incremented)
            return [organism]
