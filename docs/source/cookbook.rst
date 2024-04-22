========
Cookbook
========

On this page, we present a complete simulation structure to get started with 
Blossom. In this case, we aim to model a predator-prey dynamic.

First, we can create a basic directory structure for our project:

.. code-block:: bash

    predator-prey/
        config.yml 
        custom.py 

Your config file might look like this:

.. code-block:: yaml

    species:
      - name: predator
        population: 100
        max_age: inf
        action: predator_action
        movement: simple_random
        reproduction:
          type: pure_replication
        eating:
          type: eat_prey
          capacity: 250
          initial: 200
          metabolism: 10
          intake: 80
          days_without: 5
        linked_modules:
          - custom.py
      - name: prey
        population: 500
        max_age: inf
        action: prey_action
        movement: simple_random
        reproduction:
          type: pure_replication
        linked_modules:
          - custom.py
    world:
      dimensionality: 2
      size: [1, 100]
      water:
        peak: inf 
      food: 
        peak: inf 
      obstacles:
        peak: 0 
    timesteps: 5000
    organism_limit: 20000

This produces a 1 x 100 world (technically one-dimensional) with unlimited
resources, to focus on the organism interactions. 

The custom methods are defined in external modules, such as this in 
``custom.py``:

.. code-block:: python 

    import numpy as np

    def predator_action(organism, universe):
        if universe.rng.random() < 1/2:
            if organism.food_current > organism.food_capacity // 2:
                return 'reproduce'
            else:
                return 'eat'
        else:
            if universe.rng.random() < 2/10: # 1/10:
                return 'eat'
            else:
                return 'move'

    def eat_prey(organism, universe):
        location = tuple(organism.location)
        colocated_prey = []
        colocated_predators = []
        for org in universe.organisms_by_location[location]:
            if org.alive:
                if org.species_name == 'prey1':
                    colocated_prey.append(org)
                elif org.species_name == 'predator1':
                    colocated_predators.append(org)
        if len(colocated_prey) == 0 or len(colocated_prey) <= len(colocated_predators):
            return [organism]
        elif len(colocated_prey) == 1:
            prey = colocated_prey[0]
        else:
            prey = universe.rng.choice(colocated_prey)

        # food_from_prey = 0.8 * (prey.food_capacity)
        food_from_prey = organism.food_intake
        diff = organism.food_capacity - organism.food_current
        intake = min(food_from_prey, diff)
        organism = organism.update_parameter('food_current',
                                            intake,
                                            method='add')

        prey = prey.die('eaten')

        return [organism, prey]

    def prey_action(organism, universe):
        if universe.rng.random() < 1/30:
            return 'reproduce'
        else:
            return 'move'

Notice that in the config file, the custom methods are listed by name and 
the external modules are linked via the ``linked_modules`` keyword.

To execute simulations, we can run this command within the project directory:

.. code-block:: bash

    blossom run -s SEED 

While it isn't necessary by any means, setting a seed at runtime promotes 
reproducibility. If the run is interrupted, you can re-run this same command 
and it will attempt to continue from the last point. Otherwise, if you wish to 
restart from the beginning, run ``blossom run`` with the ``-r`` flag. 