from context import blossom

ENVIRONMENT_FN = 'generated_environment.json'

# Set up world
world_size = 100
world_block = world_size // 5

peak_water = 10000
water = ([0] * world_block
         + [peak_water] * world_block * 2
         + [0] * world_block * 2)

peak_food = 10000
food = ([0] * world_block * 2
        + [peak_water] * world_block * 2
        + [0] * world_block)

obstacles = [0] * world_size

blossom.write_environment(water,
                          food,
                          obstacles,
                          ENVIRONMENT_FN)
