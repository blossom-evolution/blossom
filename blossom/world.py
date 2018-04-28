

class World(object):
    """
    World class for the environment of the simulation.
    """

    def __init__(self, world_size=[]):
        self.world_size = world_size
        self.dimensionality = len(self.world_size)
        pass
