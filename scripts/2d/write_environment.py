from context import blossom

ENVIRONMENT_FN = 'generated_environment.json'

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
