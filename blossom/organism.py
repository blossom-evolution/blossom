import organism_classes as oc

# maybe put this in species.py? depends on use in executable
def make_organism_class(reproduction_class,
                        movement_class,
                        food_class,
                        water_class):
    class Organism(reproduction_class,
                   movement_class,
                   food_class,
                   water_class):
        pass
    return Organism

# initialization should do the randomization
organism1 = Organism(r,m,f,w)
