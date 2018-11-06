from context import blossom

WORLD_FN = None
ORGANISMS_FN = None
WORLD_PARAM_FN = 'world.param'
SPECIES_PARAM_FNS = ['species1.param']
CUSTOM_METHODS_FNS = ['custom_methods.py']
DATASET_OUTPUT_DIR = 'datasets/'
ENVIRONMENT_FN = 'generated_environment.json'

START_TIME = 0
END_TIME = 200

# Set up world
world_size = [100, 100]

peak_water = 200
water = [[peak_water // 2 for x in range(world_size[1])]
         for x in range(world_size[0])]
for i in range(world_size[0] // 2):
    water[i] = [peak_water] * world_size[1]

peak_food = 200
food = [[peak_food // 2 for x in range(world_size[1])]
        for x in range(world_size[0])]
for i in range(world_size[0] // 2):
    food[i] = [peak_food] * world_size[1]

obstacles = [[0 for x in range(world_size[1])] for x in range(world_size[0])]


blossom.write_environment(water,
                          food,
                          obstacles,
                          ENVIRONMENT_FN)

# Create universe
universe = blossom.Universe(world_fn=WORLD_FN,
                            organisms_fn=ORGANISMS_FN,
                            world_param_fn=WORLD_PARAM_FN,
                            species_param_fns=SPECIES_PARAM_FNS,
                            custom_methods_fns=CUSTOM_METHODS_FNS,
                            current_time=START_TIME,
                            end_time=END_TIME,
                            dataset_dir=DATASET_OUTPUT_DIR)

# Iterate until end of simulation
while universe.current_time < universe.end_time:
    print('t = %s: %s organisms' % (universe.current_time,
                                    len(universe.organism_list)))
    universe.step()
