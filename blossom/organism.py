import organism_classes as oc

# maybe put this in species.py? depends on use in executable
def make_organism_class(movement,
                        reproduction,
                        drinking,
                        eating):
    class Organism(movement=movement,
                   reproduction=reproduction,
                   drinking=drinking,
                   eating=eating):
        pass
    return Organism

# initialization should do the randomization
MyOrganism = make_organism_class(m,r,d,e)
organism1 = MyOrganism()
