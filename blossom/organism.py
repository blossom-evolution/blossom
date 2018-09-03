import uuid

import fields
from organism_behavior import movement, reproduction, drinking, eating, action

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

        if self.water_current is None:
            self.water_current = self.water_initial
        if self.food_current is None:
            self.food_current = self.food_initial
            
    @classmethod
    def clone(cls, organism):
        """
        Makes a new Organism object identical to the current one.
        """
        return cls(vars(organism))

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
        return getattr(self, action_name)(organism_list, world)

    def living(self):
        """
        Checks whether organism is still alive
        """
        if self.alive == False:
            return False
        if self.age > self.max_age:
            return False
        if self.drinking_type is not None and self.time_without_water > self.max_time_without_water:
            return False
        if self.eating_type is not None and self.time_without_food > self.max_time_without_food:
            return False
        return True

    def death_old_age(self):
        return self.age > self.max_age

    def death_thirst(self):
        return self.drinking_type is not None and self.time_without_water > self.max_time_without_water

    def update_state(self, organism_list, world):
        """
        Update organism's internal state (including age, water, food)
        """
        organism = self.update_age(organism_list, world)
        organism = organism.update_water(organism_list, world)
        organism = organism.update_food(organism_list, world)
        return organism

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
        return self

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
        organism = self.clone(self).update_age(organism_list, world)
        if organism.alive and not organism.death_old_age():
            # Keep acting if alive
            affected_organisms = organism.act(organism_list, world)
            for org in affected_organisms:
                org = org.update_water(organism_list, world)
                org = org.update_food(organism_list, world)
                if org.death_thirst():
                    org = org.die('thirst')
            return affected_organisms
        elif organism.alive:
            # If living status hasn't been updated, update it
            return [organism.die('old_age')]
        else:
            # Organism status already set to dead, so return organism
            # (with 'age' incremented)
            return [organism]
