import uuid
import copy
import imp
import sys

import fields
from utils import cast_to_list
from organism_behavior import movement, reproduction, drinking, eating, action


class Organism(object):
    """
    A basic organism structure for all species.
    """

    def __init__(self, init_dict={}):
        """
        Create a new organism from a dictary of parameters. The dictionary
        is specified in blossom.fields.
        """
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

        Parameters
        ----------
        organism : Organism
            Organism to copy.

        Returns
        -------
        new_organism : Organism
            Copied organism.
        """
        new_organism = cls(vars(organism))
        # Use copy module to properly handle mutable lists
        new_organism.ancestry = copy.copy(new_organism.ancestry)
        new_organism.position = copy.copy(new_organism.position)
        return new_organism

    def update_parameter(self, parameter, value, method='set'):
        """
        Update a specific parameter of the organism.

        Parameters
        ----------
        parameter : string
            Parameter to update.
        value
            Value with which to update.
        method : string
            Method types are: 'set', 'add', 'subtract'.

        Returns
        -------
        self : Organism
            Same organism object with updated parameter.
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
        """
        Method for handling movement. Searches through custom methods and
        built-in movement methods.

        Parameters
        ----------
        organism_list : list of Organisms
            List of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's movement.

        """
        if self.movement_type is None:
            sys.exit('No movement type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.movement_type):
                    return (getattr(custom_module, self.movement_type)
                            (self, organism_list, world))
        return (getattr(movement, self.movement_type)
                (self, organism_list, world))

    def reproduce(self, organism_list, world):
        """
        Method for handling reproduction. Searches through custom methods
        and built-in reproduction methods.

        Parameters
        ----------
        organism_list : list of Organisms
            List of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's
            reproduction. For example, this would include both parent and
            child organisms.

        """
        if self.reproduction_type is None:
            sys.exit('No reproduction type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.reproduction_type):
                    return (getattr(custom_module, self.reproduction_type)
                            (self, organism_list, world))
        return (getattr(reproduction, self.reproduction_type)
                (self, organism_list, world))

    def drink(self, organism_list, world):
        """
        Method for handling drinking. Searches through custom methods and
        built-in drinking methods.

        Parameters
        ----------
        organism_list : list of Organisms
            List of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's drinking.

        """
        if self.drinking_type is None:
            sys.exit('No drinking type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.drinking_type):
                    return (getattr(custom_module, self.drinking_type)
                            (self, organism_list, world))
        return (getattr(drinking, self.drinking_type)
                (self, organism_list, world))

    def eat(self, organism_list, world):
        """
        Method for handling eating. Searches through custom methods and
        built-in eating methods.

        Parameters
        ----------
        organism_list : list of Organisms
            List of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's eating.

        """
        if self.eating_type is None:
            sys.exit('No eating type defined!')
        elif self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.eating_type):
                    return (getattr(custom_module, self.eating_type)
                            (self, organism_list, world))
        return getattr(eating, self.eating_type)(self, organism_list, world)

    def act(self, organism_list, world):
        """
        Method that decides and calls an action for the current timestep.
        Searches through custom methods and built-in movement methods.
        The action method specifically selects an action to take, from "move",
        "reproduce", "drink", and "eat". Then the appropriate instance method
        from this class is executed to yield the final list of affect
        organisms.

        Parameters
        ----------
        organism_list : list of Organisms
            List of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.

        Returns
        -------
        affected_organisms : list of Organisms
            Organism or list of organisms affected by this organism's action.

        """
        action_name = None
        if self.custom_methods_fns is not None:
            for custom_module in self.custom_modules:
                if hasattr(custom_module, self.action_type):
                    action_name = (getattr(custom_module, self.action_type)
                                   (self, organism_list, world))
        if action_name is None:
            action_name = (getattr(action, self.action_type)
                           (self, organism_list, world))
        return cast_to_list(getattr(self, action_name)(organism_list, world))

    def update_age(self):
        """
        Increments age by 1.
        """
        return self.update_parameter('age', 1, 'add')

    def update_water(self):
        """
        Updates health parameters relevant to water consumption.

        Decreases current water level based on metabolism, and increments
        time without water accordingly. Note that organisms die of thirst if
        this reaches the maximum time without water.
        """
        self.water_current -= self.water_metabolism

        if self.water_current > self.water_capacity:
            self.water_current = self.water_capacity
        elif self.water_current <= 0:
            self.water_current = 0
            self.time_without_water += 1
        elif self.time_without_water > 0:
            self.time_without_water = 0
        return self

    def update_food(self):
        """
        Updates health parameters relevant to food consumption.

        Decreases current food level based on metabolism, and increments
        time without food accordingly. Note that organisms die of hunger if
        this reaches the maximum time without food.
        """
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
        """
        Check various conditions for death.

        Parameters
        ----------
        cause : str
            Potential cause of this organism's death.

        Returns
        -------
        is_dead : bool
            Returns True if organism is dead from the specified cause, False
            otherwise.
        """
        if cause == 'old_age':
            return self.age > self.max_age
        elif cause == 'thirst':
            return (self.drinking_type is not None
                    and self.time_without_water > self.max_time_without_water)
        elif cause == 'hunger':
            return (self.eating_type is not None
                    and self.time_without_food > self.max_time_without_food)
        else:
            sys.exit('Invalid cause!')

    def die(self, cause):
        """
        Method that "kills" organism.

        Parameters
        ----------
        cause : str
            Cause of this organism's death.

        Returns
        -------
        dead_organism : Organism
            New "dead" state of this organism.
        """
        self.update_parameter('alive', False)
        self.update_parameter('age_at_death', self.age)
        self.update_parameter('cause_of_death', cause)
        return self

    def step(self, organism_list, world):
        """
        Steps through one time step for this organism. Reflects changes
        based on actions / behaviors and updates to health parameters.

        Returns a list of organisms that the action produced (either new or
        altered organisms).

        Parameters
        ----------
        organism_list : list of Organisms
            List of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.

        Returns
        -------
        affected_organisms : list of Organisms
            Organism or list of organisms affected by this organism's actions
            or health. This could be an updated version of this organism,
            especially if the organism dies during the time step, but could
            also be multiple other organisms affected by actions (i.e. children
            from reproduction).

        """
        # Create new Organism object / reference and update age
        organism = self.clone(self).update_age()
        if organism.alive:
            if not organism.at_death('old_age'):
                # Update health
                if organism.drinking_type is not None:
                    organism.update_water()
                if organism.eating_type is not None:
                    organism.update_food()

                # Keep acting if alive
                affected_organisms = organism.act(organism_list, world)

                # Check water / food status
                if organism.drinking_type is not None:
                    if organism.at_death('thirst'):
                        organism.die('thirst')
                if organism.eating_type is not None:
                    if organism.at_death('hunger'):
                        organism.die('hunger')

                return affected_organisms
            else:
                # This organism is at death from old age
                return [organism.die('old_age')]
        else:
            # Organism status already set to dead, so return organism
            # (with 'age' incremented)
            return [organism]
