from . import default_fields


class World(object):
    """
    World class for the environment of the simulation.
    """

    def __init__(self, init_dict={}):
        """
        Create a new world from a dictary of parameters. The dictionary
        is specified in blossom.default_fields.
        """
        # Set up defaults based on world parameters
        for (field, default) in default_fields.world_fields.items():
            setattr(self, field, init_dict.get(field, default))

        # Set up custom fields provided in initializaiton dictionary
        init_keys = set(init_dict.keys())
        default_keys = set(default_fields.world_fields.keys())
        for custom_field in (init_keys - default_keys):
            setattr(self, custom_field, init_dict[custom_field])

    def to_dict(self):
        """
        Convert World to dict.
        """
        world_vars = vars(self)
        public_vars = {key: val
                       for key, val in world_vars.items()
                       if not key.startswith('_')}
        return public_vars

    def step(self):
        self.current_time += 1
