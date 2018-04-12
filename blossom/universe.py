

class Universe(object):
    """
    Create the universe of the simulation.
    """

    def __init__(self):
        self.load_species_parameters()
        self.load_world_parameters()
        self.write_organism_dataset()
        self.write_world_dataset()
        pass

    def load_species_parameters(self):
        pass

    def load_world_parameters(self):
        pass

    def write_organism_dataset(self):
        pass

    def write_world_dataset(self):
        pass

    def step(self):
        pass
