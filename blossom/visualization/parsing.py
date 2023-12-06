import json
import glob
from pathlib import Path

import matplotlib  
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt
import numpy as np

from blossom import dataset_io
from blossom import population_funcs


def read_log(fn):
    with open(fn, 'r') as f:
        return json.load(f)


class Snapshot(object):
    """
    Single time snapshot of universe.
    """

    def __init__(self, dataset_fn):
        self.population_dict, self.world, _ = dataset_io.load_universe(dataset_fn)
        self.organisms_by_location = population_funcs.hash_by_location(
            population_funcs.get_organism_list(self.population_dict)
        )
        self.current_time = self.world.current_time

    def plot_2d(self, label, attr_func):
        """
        attr_func is a function that accepts a Snapshot object and a location,
        and returns a quantity
        """
        temp_img = np.zeros(shape=self.world.world_size)
        for i in range(temp_img.shape[0]):
            for j in range(temp_img.shape[1]):
                temp_img[i][j] += attr_func(ds=self,
                                            loc=(i, j))

        plt.title(label)
        plt.imshow(temp_img, interpolation='none')
        plt.colorbar()


class TimeSeries(object):
    """
    Series of dataset objects for iterating over.
    """

    def __init__(self, dataset_dir):
        self.dataset_dir = Path(dataset_dir)
        self.dataset_fns = sorted(self.dataset_dir.glob('*.json'))
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            ds = Snapshot(self.dataset_fns[self.index])
        except IndexError:
            raise StopIteration
        self.index += 1
        return ds

    def plot_ts(self, attr_funcs):
        """
        attr_funcs is a list of tuples (label, function), where the function
        calculates desired attributes given a Snapshot at each timestep in the
        simulation.
        """
        attr_vals = {label: [] for label, func in attr_funcs}
        for ds_fn in self.dataset_fns:
            ds = Snapshot(ds_fn)
            for label, attr_func in attr_funcs:
                attr_vals[label].append(attr_func(ds))

        for label in attr_vals:
            plt.plot(attr_vals[label], label=label)
        plt.plot([0] * len(attr_vals[label]), 'k--')

        plt.xlabel('Timestep')
        plt.ylabel('Count')
        plt.legend()
