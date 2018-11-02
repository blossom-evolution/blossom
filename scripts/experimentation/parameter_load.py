from context import blossom

WORLD_FN = None
ORGANISMS_FN = None
WORLD_PARAM_FN = 'world.param'
SPECIES_PARAM_FNS = ['species1.param']
CUSTOM_METHODS_FNS = ['/Users/bryanbrzycki/Documents/Personal/'
                      + 'Evolution-Code/Code/blossom/scripts/experimentation/'
                      + 'custom_methods.py']
DATASET_OUTPUT_DIR = 'datasets/fix_negatives/'

START_TIME = 0
END_TIME = 10

world_size = 1

peak_water = 2
water = [peak_water] * world_size

peak_food = 0
food = [0] * world_size

blossom.write_environment(water,
                          food,
                          [0] * world_size,
                          'generated_environment.json')

universe = blossom.Universe(world_fn=WORLD_FN,
                            organisms_fn=ORGANISMS_FN,
                            world_param_fn=WORLD_PARAM_FN,
                            species_param_fns=SPECIES_PARAM_FNS,
                            custom_methods_fns=CUSTOM_METHODS_FNS,
                            current_time=START_TIME,
                            end_time=END_TIME,
                            dataset_dir=DATASET_OUTPUT_DIR)

while universe.current_time < universe.end_time:
    print('t = %s: %s organisms' % (universe.current_time,
                                    len(universe.organism_list)))
    universe.step()
