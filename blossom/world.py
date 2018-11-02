import fields


class World(object):
    """
    World class for the environment of the simulation.
    """

    def __init__(self, init_dict={}):
        """
        Create a new world from a dictary of parameters. The dictionary
        is specified in blossom.fields.
        """
        for (prop, default) in fields.world_field_names.items():
            setattr(self, prop, init_dict.get(prop, default))
