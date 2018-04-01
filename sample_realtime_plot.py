#!/usr/bin/env python

import numpy as np
import time
import matplotlib
from matplotlib import pyplot as plt
from matplotlib import collections  as mc


def randomwalk(dims=(250, 250), n=1, sigma=5, alpha=0.8, seed=1):
    """ A simple random walk with memory """

    r, c = dims
    # gen = np.random.RandomState(seed)
    gen = np.random.RandomState()
    pos = gen.rand(2, n) * ((r,), (c,))
    old_delta = gen.randn(2, n) * sigma

    while True:
        delta = (1. - alpha) * gen.randn(2, n) * sigma + alpha * old_delta
        pos += delta
        for ii in range(n):
            if not (0. <= pos[0, ii]):
                pos[0, ii] = abs(pos[0, ii])
            if not (pos[0, ii] < r):
                pos[0, ii] = r - abs(pos[0, ii] - r)
            if not (0. <= pos[1, ii]):
                pos[1, ii] = abs(pos[1, ii])
            if not (pos[1, ii] < c):
                pos[1, ii] = c - abs(pos[1, ii] - c)
        old_delta = delta
        yield pos


def run(niter=1000, n=1, seed=1, filename='plot.png'):
    """
    Display the simulation using matplotlib, optionally using blit for speed
    """
    gen = np.random.RandomState()
    rgb = gen.rand(n, 3)

    #plt.ion()
    index = 0

    fig, ax = plt.subplots(1, 1)
    ax.set_aspect('equal')
    ax.set_xlim(0, 250)
    ax.set_ylim(0, 250)
    rw = randomwalk(n=n)
    x, y = next(rw)
    #points = ax.plot(x, y, '.', color=rgb)
    text = ax.text(0.05, 1.05, "t = %s" % str(index), horizontalalignment='left',
        verticalalignment='center', transform=ax.transAxes)

    for ii in range(niter):
        x_old = []
        y_old = []
        index += 1
        # update the xy data
        for i in range(len(x)):
            x_old.append(x[i])
            y_old.append(y[i])
        x, y = next(rw)
        #lc = mc.LineCollection([[(x_old[0],y_old[0]),(x[0],y[0])]], linewidths=1)
        for i in range(len(x)):
            ax.plot([x_old[i],x[i]],[y_old[i],y[i]], '-', color=rgb[i],
                linewidth=1)
        #ax.plot(x, y, 'k.')[0]
        #ax.add_collection(lc)
        text.set_text("t = %s" % str(index))
        print(index)
        #plt.pause(0.000001)
    plt.savefig(filename)
    plt.close(fig)

if __name__ == '__main__':
    for i in range(10):
        run(niter=1000, n=10, filename='images/%s.png' % i)
