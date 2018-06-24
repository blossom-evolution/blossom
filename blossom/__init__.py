"""
blossom is a package for simulating evolution
"""

__version__ = "0.1"

import sys
import os
sys.path.append(os.path.dirname(__file__))

from universe import Universe
from organism import Organism
from world import World
