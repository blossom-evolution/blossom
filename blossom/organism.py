import uuid
import copy
import imp
import sys

import default_fields
from utils import cast_to_list
from organism_behavior import movement, reproduction, drinking, eating, action


class Organism(object):
    """
    A basic organism structure for all species.
    """

    def __init__(self, init_dict={}):
        """
        Create a new organism from a dictary of parameters. The dictionary
        is specified in blossom.default_fields.
        """
        # Set up defaults based on organism parameters
        for (field, default) in default_fields.organism_fields.items():
            setattr(self, field, init_dict.get(field, default))

        # Set up custom fields provided in initialization dictionary
        init_keys = set(init_dict.keys())
        default_keys = set(default_fields.organism_fields.keys())
        for custom_field in (init_keys - default_keys):
            setattr(self, custom_field, init_dict[custom_field])

        # Set unique id for organism
        if self.organism_id is None:
            self.organism_id = str(uuid.uuid4())

        # Set current water level for uninitialized organism
        if self.drinking_type is not None and self.water_current is None:
            self.water_current = self.water_initial

        # Set current food level for uninitialized organism
        if self.eating_type is not None and self.food_current is None:
            self.food_current = self.food_initial

        # Import custom modules / paths
        if self.custom_module_fns is not None:
            self._custom_modules = []
            for i, path in enumerate(cast_to_list(self.custom_module_fns)):
                temp_module = imp.load_source('%s' % i, path)
                self._custom_modules.append(temp_module)

    def to_dict(self):
        """
        Convert Organism to dict.
        """
        organism_vars = vars(self)
        public_vars = {key: val
                       for key, val in organism_vars.items()
                       if not key.startswith('_')}
        return public_vars

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
        new_organism = cls(organism.to_dict())
        # Use copy module to properly handle mutable lists
        new_organism.ancestry = copy.copy(new_organism.ancestry)
        new_organism.position = copy.copy(new_organism.position)
        return new_organism

    def clone_self(self):
        """
        Clone this organism.
        """
        return self.clone(self)

    def update_parameter(self, parameter, value, method='set', in_place=False, original=None):
        """
        Update a specific parameter of the organism.

        Parameters
        ----------
        parameter : string
            Parameter to update.
        value
            Value with which to update.
        method : string
            Method types are: 'set', 'add', 'subtract', 'append'.
        in_place : bool
            If True, modifies self, otherwise, copy organism and return new
            Organism object.
        original : Organism or None
            Original organism we are changing. If it is the original,
            clone organism so that we aren't editing the original.

        Returns
        -------
        updated_organism : Organism
            Organism object with updated parameter.
        """
        if self is original or not in_place:
            updated_organism = self.clone_self()
        else:
            updated_organism = self
        attribute = getattr(updated_organism, parameter)
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
        setattr(updated_organism, parameter, attribute)
        return updated_organism

    def move(self, population_dict, world, position_hash_table=None):
        """
        Method for handling movement. Searches through custom methods and
        built-in movement methods.

        Parameters
        ----------
        population_dict : dict of Organisms
            Dict of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.
        position_hash_table : dict
            Dictionary mapping positions to available organisms.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's movement.
        """
        try:
            if self.movement_type is None:
                sys.exit('No movement type defined!')
            elif self.custom_module_fns is not None:
                for custom_module in self._custom_modules:
                    if hasattr(custom_module, self.movement_type):
                        return getattr(custom_module, self.movement_type)(
                            self,
                            population_dict,
                            world,
                            position_hash_table=position_hash_table
                        )
            return getattr(movement, self.movement_type)(
                self,
                population_dict,
                world,
                position_hash_table=position_hash_table
            )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.movement_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def reproduce(self, population_dict, world, position_hash_table=None):
        """
        Method for handling reproduction. Searches through custom methods
        and built-in reproduction methods.

        Parameters
        ----------
        population_dict : dict of Organisms
            Dict of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.
        position_hash_table : dict
            Dictionary mapping positions to available organisms.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's
            reproduction. For example, this would include both parent and
            child organisms.

        """
        try:
            if self.reproduction_type is None:
                sys.exit('No reproduction type defined!')
            elif self.custom_module_fns is not None:
                for custom_module in self._custom_modules:
                    if hasattr(custom_module, self.reproduction_type):
                        return getattr(custom_module, self.reproduction_type)(
                            self,
                            population_dict,
                            world,
                            position_hash_table=position_hash_table
                        )
            return getattr(reproduction, self.reproduction_type)(
                self,
                population_dict,
                world,
                position_hash_table=position_hash_table
            )
        except AttributeError as e:
            raise AttributeError(
                str(e) + '. Check '
                + 'that \'%s\' method is indeed ' % self.reproduction_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def drink(self, population_dict, world, position_hash_table=None):
        """
        Method for handling drinking. Searches through custom methods and
        built-in drinking methods.

        Parameters
        ----------
        population_dict : dict of Organisms
            Dict of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.
        position_hash_table : dict
            Dictionary mapping positions to available organisms.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's drinking.

        """
        try:
            if self.drinking_type is None:
                sys.exit('No drinking type defined!')
            elif self.custom_module_fns is not None:
                for custom_module in self._custom_modules:
                    if hasattr(custom_module, self.drinking_type):
                        return getattr(custom_module, self.drinking_type)(
                            self,
                            population_dict,
                            world,
                            position_hash_table=position_hash_table
                        )
            return getattr(drinking, self.drinking_type)(
                self,
                population_dict,
                world,
                position_hash_table=position_hash_table
            )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.drinking_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def eat(self, population_dict, world, position_hash_table=None):
        """
        Method for handling eating. Searches through custom methods and
        built-in eating methods.

        Parameters
        ----------
        population_dict : dict of Organisms
            Dict of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.
        position_hash_table : dict
            Dictionary mapping positions to available organisms.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's eating.

        """
        try:
            if self.eating_type is None:
                sys.exit('No eating type defined!')
            elif self.custom_module_fns is not None:
                for custom_module in self._custom_modules:
                    if hasattr(custom_module, self.eating_type):
                        return getattr(custom_module, self.eating_type)(
                            self,
                            population_dict,
                            world,
                            position_hash_table=position_hash_table
                        )
            return getattr(eating, self.eating_type)(
                self,
                population_dict,
                world,
                position_hash_table=position_hash_table
            )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.eating_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def act(self, population_dict, world, position_hash_table=None):
        """
        Method that decides and calls an action for the current timestep.
        Searches through custom methods and built-in movement methods.
        The action method specifically selects an action to take, from "move",
        "reproduce", "drink", and "eat". Then the appropriate instance method
        from this class is executed to yield the final list of affect
        organisms.

        Parameters
        ----------
        population_dict : dict of Organisms
            Dict of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.
        position_hash_table : dict
            Dictionary mapping positions to available organisms.

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's action.

        """
        action_name = None
        try:
            if self.custom_module_fns is not None:
                for custom_module in self._custom_modules:
                    if hasattr(custom_module, self.action_type):
                        action_name = getattr(custom_module, self.action_type)(
                            self,
                            population_dict,
                            world,
                            position_hash_table=position_hash_table
                        )
            if action_name is None:
                action_name = getattr(action, self.action_type)(
                    self,
                    population_dict,
                    world,
                    position_hash_table=position_hash_table
                )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.action_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

        self.last_action = action_name

        affected_organisms = cast_to_list(getattr(self, action_name)(
            population_dict,
            world,
            position_hash_table=position_hash_table
        ))

        # Ensure this organism is included in affected_organisms
        already_included = False
        for org in affected_organisms:
            if org.organism_id == self.organism_id:
                already_included = True
        if not already_included:
            # e.g. unknown reason for exlusion, so default to death
            self.die('unknown', in_place=True)
            affected_organisms.append(self)

        return self, affected_organisms

    def _update_age(self):
        """
        Increments age by 1.
        """
        self.age += 1
        return self

    def _update_water(self):
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

    def _update_food(self):
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

    def is_at_death(self, cause):
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

    def die(self, cause, in_place=False, original=None):
        """
        Method that "kills" organism.

        Parameters
        ----------
        cause : str
            Cause of this organism's death.
        in_place : bool
            If True, modifies self, otherwise, copy organism and return new
            Organism object.

        Returns
        -------
        dead_organism : Organism
            New "dead" state of this organism.
        """
        updated_organism = self.update_parameter('alive',
                                                 False,
                                                 in_place=in_place,
                                                 original=original)
        updated_organism = updated_organism.update_parameter('age_at_death',
                                                             self.age,
                                                             in_place=in_place,
                                                             original=original)
        updated_organism = updated_organism.update_parameter('cause_of_death',
                                                             cause,
                                                             in_place=in_place,
                                                             original=original)
        return updated_organism

    def step(self, population_dict, world, position_hash_table=None, do_action=True):
        """
        Steps through one time step for this organism. Reflects changes
        based on actions / behaviors and updates to health parameters.

        Returns a list of organisms that the action produced (either new or
        altered organisms).

        Parameters
        ----------
        population_dict : dict of Organisms
            Dict of organisms, with which this organism may interact.
        world : World
            World, with which this organism may interact.
        position_hash_table: dict
            Dictionary of organisms "hashed" by position.
        do_action: bool
            If True, this organism will act, otherwise, it will not.

        Returns
        -------
        affected_organisms : list of Organisms
            List of organisms affected by this organism's actions
            or health. This could be an updated version of this organism,
            especially if the organism dies during the time step, but could
            also be multiple other organisms affected by actions (i.e. children
            from reproduction).

        """
        # Create new Organism object / reference and update age
        organism = self.clone_self()._update_age()

        if organism.is_at_death('old_age'):
            # This organism is at death from old age
            # Design choice to prevent action if organism is at old age limit
            return [organism.die('old_age')]

        if do_action:
            organism, affected_organisms = organism.act(
                population_dict,
                world,
                position_hash_table=position_hash_table
            )
        else:
            affected_organisms = [organism]

        for organism in affected_organisms:
            # Checks whether alive after action
            if organism.alive:
                if organism.is_at_death('old_age'):
                    organism.die('old_age', in_place=True)

                # Update and check water / food status
                if organism.drinking_type is not None:
                    organism._update_water()
                    if organism.is_at_death('thirst'):
                        organism.die('thirst', in_place=True)

                if organism.eating_type is not None:
                    organism._update_food()
                    if organism.is_at_death('hunger'):
                        organism.die('hunger', in_place=True)

        return affected_organisms

    def step_without_acting(self):
        """
        Steps through one time step without acting for this organism.

        Returns
        -------
        organism
            Note that this returns an Organism object, not a list.

        """
        return self.step(population_dict=None,
                         world=None,
                         position_hash_table=None,
                         do_action=False)[0]
