import uuid
import copy
import sys
import importlib.util
import os
from types import ModuleType
from typing import Any, Callable
import numpy as np

from . import default_fields
from . import intent_api
from .utils import cast_to_list
from .organism_behavior import movement, reproduction, drinking, eating, action


class Organism(object):
    """
    A basic organism structure for all species.
    """
    _CUSTOM_MODULE_CACHE: dict[tuple[str, int], ModuleType] = {}
    _IMMUTABLE_SCALAR_TYPES: tuple[type, ...] = (
        bool,
        int,
        float,
        complex,
        str,
        bytes,
        type(None),
    )

    @staticmethod
    def _load_custom_module(path: str) -> ModuleType:
        """
        Load a custom behavior module from a file path.
        """
        module_path = os.path.abspath(path)
        if not os.path.isfile(module_path):
            raise FileNotFoundError(f'Custom module does not exist: {module_path}')

        mtime_ns = os.stat(module_path).st_mtime_ns
        cache_key = (module_path, mtime_ns)
        if cache_key in Organism._CUSTOM_MODULE_CACHE:
            return Organism._CUSTOM_MODULE_CACHE[cache_key]

        # Drop stale entries for this path when file has changed.
        stale_keys = [
            key
            for key in Organism._CUSTOM_MODULE_CACHE.keys()
            if key[0] == module_path and key != cache_key
        ]
        for key in stale_keys:
            del Organism._CUSTOM_MODULE_CACHE[key]

        module_name = f'blossom_custom_{uuid.uuid4().hex}'
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f'Could not load custom module from path: {module_path}')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        Organism._CUSTOM_MODULE_CACHE[cache_key] = module
        return module

    def __init__(self, init_dict={}, seed=None):
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
            self.organism_id = self.get_new_id(seed=seed)

        # Set current water level for uninitialized organism
        if self.drinking_type is not None and self.water_current is None:
            self.water_current = self.water_initial

        # Set current food level for uninitialized organism
        if self.eating_type is not None and self.food_current is None:
            self.food_current = self.food_initial

        # Import custom modules / paths
        if self.custom_module_fns is not None:
            self._custom_modules = []
            for path in cast_to_list(self.custom_module_fns):
                temp_module = self._load_custom_module(path)
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

    def get_new_id(self, seed=None):
        """
        Generates pseudo-random ID for the organism, seeded by the universe.
        """
        rng = np.random.default_rng(seed)
        return str(uuid.UUID(bytes=rng.bytes(16)))

    @classmethod
    def _clone_attribute_value(cls, value: Any) -> Any:
        """
        Clone an organism attribute value with strong mutable-isolation rules.

        Lists, dicts, sets, and tuples are recursively cloned so the cloned
        organism never shares those containers with the source organism.
        Module references are intentionally reused, since modules are loaded
        code objects and not mutable simulation state.
        """
        if isinstance(value, ModuleType):
            return value
        if isinstance(value, cls._IMMUTABLE_SCALAR_TYPES):
            return value
        if isinstance(value, list):
            return [cls._clone_attribute_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls._clone_attribute_value(item) for item in value)
        if isinstance(value, dict):
            return {
                cls._clone_attribute_value(key): cls._clone_attribute_value(item)
                for key, item in value.items()
            }
        if isinstance(value, set):
            return {cls._clone_attribute_value(item) for item in value}
        if isinstance(value, frozenset):
            return frozenset(cls._clone_attribute_value(item) for item in value)

        try:
            return copy.deepcopy(value)
        except Exception as exc:
            raise TypeError(
                'Unable to clone organism attribute '
                f'{value!r} (type={type(value).__name__}). '
                'Custom attributes must be deepcopy-compatible.'
            ) from exc

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
        # Fast-path clone: bypass __init__ reconstruction and copy attributes
        # directly while deeply isolating mutable simulation state.
        new_organism = cls.__new__(cls)
        new_organism.__dict__ = {
            field_name: cls._clone_attribute_value(field_value)
            for field_name, field_value in organism.__dict__.items()
        }
        return new_organism

    def clone_self(self):
        """
        Clone this organism.
        """
        return self.clone(self)

    def get_child(self, other_parent=None, seed=None):
        """
        Creates an Organism object with similar properties to self, and can
        add another parent if it exists. Note that this doesn't assume
        anything about how much food / water the child is left with, so these
        should be set with custom / default reproduction methods.

        Parameters
        ----------
        other_parent : Organism
            Parent that reproduces with self to produce the child.

        Returns
        -------
        child : Organism
            Generated child.
        """
        child = self.clone_self()
        child.age = 0
        child.organism_id = child.get_new_id(seed=seed)
        if other_parent is None:
            child.ancestry.append(self.organism_id)
        else:
            child.ancestry.append([self.organism_id, other_parent.organism_id])
        child.last_action = None
        return child

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
            raise ValueError('Invalid update method!')
        setattr(updated_organism, parameter, attribute)
        return updated_organism

    def _invoke_custom_callback(self, callback: Callable[..., Any], universe: Any) -> Any:
        """
        Invoke a custom callback in legacy or intent mode.
        """
        return intent_api.invoke_behavior_callback(
            callback=callback,
            actor=self,
            universe=universe
        )

    def _normalize_behavior_output(self, output: Any, universe: Any) -> list["Organism"]:
        """
        Normalize callback output into a concrete organism list.
        """
        return intent_api.normalize_effect_output(
            output=output,
            actor=self,
            universe=universe
        )

    def _run_behavior_method(self, method_name: str | None, builtin_module: Any, universe: Any) -> list["Organism"]:
        """
        Resolve and execute a behavior callback by name.

        Search order:
        1) custom modules (if linked)
        2) built-in behavior module
        """
        if method_name is None:
            raise ValueError('No method type defined!')

        if self.custom_module_fns is not None:
            for custom_module in self._custom_modules:
                if hasattr(custom_module, method_name):
                    callback = getattr(custom_module, method_name)
                    output = self._invoke_custom_callback(callback, universe)
                    return self._normalize_behavior_output(output, universe)

        output = getattr(builtin_module, method_name)(self, universe)
        # Built-ins are engine-owned and expected to return organism objects.
        # Keep this fast path to avoid repeated validation overhead.
        if isinstance(output, (list, tuple)):
            return list(output)
        return [output]

    def move(self, universe):
        """
        Method for handling movement. Searches through custom methods and
        built-in movement methods.

        Parameters
        ----------
        universe : Universe
            Universe containing organism

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's movement.
        """
        try:
            return self._run_behavior_method(
                method_name=self.movement_type,
                builtin_module=movement,
                universe=universe
            )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.movement_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def reproduce(self, universe):
        """
        Method for handling reproduction. Searches through custom methods
        and built-in reproduction methods.

        Parameters
        ----------
        universe : Universe
            Universe containing organism

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's
            reproduction. For example, this would include both parent and
            child organisms.

        """
        try:
            return self._run_behavior_method(
                method_name=self.reproduction_type,
                builtin_module=reproduction,
                universe=universe
            )
        except AttributeError as e:
            raise AttributeError(
                str(e) + '. Check '
                + 'that \'%s\' method is indeed ' % self.reproduction_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def drink(self, universe):
        """
        Method for handling drinking. Searches through custom methods and
        built-in drinking methods.

        Parameters
        ----------
        universe : Universe
            Universe containing organism

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's drinking.

        """
        try:
            return self._run_behavior_method(
                method_name=self.drinking_type,
                builtin_module=drinking,
                universe=universe
            )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.drinking_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def eat(self, universe):
        """
        Method for handling eating. Searches through custom methods and
        built-in eating methods.

        Parameters
        ----------
        universe : Universe
            Universe containing organism

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's eating.

        """
        try:
            return self._run_behavior_method(
                method_name=self.eating_type,
                builtin_module=eating,
                universe=universe
            )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.eating_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

    def act(self, universe):
        """
        Method that decides and calls an action for the current timestep.
        Searches through custom methods and built-in movement methods.
        The action method specifically selects an action to take, from "move",
        "reproduce", "drink", and "eat". Then the appropriate instance method
        from this class is executed to yield the final list of affect
        organisms.

        Parameters
        ----------
        universe : Universe
            Universe containing organism

        Returns
        -------
        affected_organisms : Organisms, or list of Organisms
            Organism or list of organisms affected by this organism's action.

        """
        action_result = None
        try:
            if self.custom_module_fns is not None:
                for custom_module in self._custom_modules:
                    if hasattr(custom_module, self.action_type):
                        callback = getattr(custom_module, self.action_type)
                        action_result = self._invoke_custom_callback(
                            callback=callback,
                            universe=universe
                        )
                        break
            if action_result is None:
                action_result = getattr(action, self.action_type)(
                    self,
                    universe
                )
        except AttributeError as e:
            raise AttributeError(
                str(e)
                + '. Check that \'%s\' method is indeed ' % self.action_type
                + 'contained within the provided custom modules and that the '
                + 'method is written correctly.'
            ).with_traceback(sys.exc_info()[2])

        if isinstance(action_result, str):
            self.last_action = action_result
            affected_organisms = cast_to_list(getattr(self, action_result)(universe))
        else:
            self.last_action = self.action_type
            affected_organisms = self._normalize_behavior_output(
                output=action_result,
                universe=universe
            )

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
            raise ValueError('Invalid cause!')

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

    def step(self, universe, do_action=True):
        """
        Steps through one time step for this organism. Reflects changes
        based on actions / behaviors and updates to health parameters.

        Returns a list of organisms that the action produced (either new or
        altered organisms).

        Parameters
        ----------
        universe : Universe
            Universe containing organism
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
            organism, affected_organisms = organism.act(universe)
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
        return self.step(universe=None, do_action=False)[0]
