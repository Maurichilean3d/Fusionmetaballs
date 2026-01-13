# Metaballs.py
# Sistema Metaballs COMPLETO tipo Blender para Fusion 360

import adsk.core
import adsk.fusion
import math
import os
import struct
import tempfile
import traceback
import threading
import time

from .lib import fusion360utils as futil
from . import config

_handlers = []
_monitor_thread = None
_monitoring = False

CMD_ID_ADD = f"{config.CMD_ID}_add"
CMD_ID_SETTINGS = f"{config.CMD_ID}_settings"
CMD_ID_DELETE = f"{config.CMD_ID}_delete"

ATTR_GROUP = "MetaballsSystem"
ATTR_METABALL = "metaball"
ATTR_FAMILY = "family"
ATTR_INFLUENCE = "influence"

# Settings
_settings = {
    "iso": 1.0,
    "resolution": 40,
    "auto_update": True,
    "update_delay": 0.3
}


# ============= MARCHING CUBES COMPLETO =============

EDGE_TABLE = [
    0x0, 0x109, 0x203, 0x30a, 0x406, 0x50f, 0x605, 0x70c,
    0x80c, 0x905, 0xa0f, 0xb06, 0xc0a, 0xd03, 0xe09, 0xf00,
    0x190, 0x99, 0x393, 0x29a, 0x596, 0x49f, 0x795, 0x69c,
    0x99c, 0x895, 0xb9f, 0xa96, 0xd9a, 0xc93, 0xf99, 0xe90,
    0x230, 0x339, 0x33, 0x13a, 0x636, 0x73f, 0x435, 0x53c,
    0xa3c, 0xb35, 0x83f, 0x936, 0xe3a, 0xf33, 0xc39, 0xd30,
    0x3a0, 0x2a9, 0x1a3, 0xaa, 0x7a6, 0x6af, 0x5a5, 0x4ac,
    0xbac, 0xaa5, 0x9af, 0x8a6, 0xfaa, 0xea3, 0xda9, 0xca0,
    0x460, 0x569, 0x663, 0x76a, 0x66, 0x16f, 0x265, 0x36c,
    0xc6c, 0xd65, 0xe6f, 0xf66, 0x86a, 0x963, 0xa69, 0xb60,
    0x5f0, 0x4f9, 0x7f3, 0x6fa, 0x1f6, 0xff, 0x3f5, 0x2fc,
    0xdfc, 0xcf5, 0xfff, 0xef6, 0x9fa, 0x8f3, 0xbf9, 0xaf0,
    0x650, 0x759, 0x453, 0x55a, 0x256, 0x35f, 0x55, 0x15c,
    0xe5c, 0xf55, 0xc5f, 0xd56, 0xa5a, 0xb53, 0x859, 0x950,
    0x7c0, 0x6c9, 0x5c3, 0x4ca, 0x3c6, 0x2cf, 0x1c5, 0xcc,
    0xfcc, 0xec5, 0xdcf, 0xcc6, 0xbca, 0xac3, 0x9c9, 0x8c0,
    0x8c0, 0x9c9, 0xac3, 0xbca, 0xcc6, 0xdcf, 0xec5, 0xfcc,
    0xcc, 0x1c5, 0x2cf, 0x3c6, 0x4ca, 0x5c3, 0x6c9, 0x7c0,
    0x950, 0x859, 0xb53, 0xa5a, 0xd56, 0xc5f, 0xf55, 0xe5c,
    0x15c, 0x55, 0x35f, 0x256, 0x55a, 0x453, 0x759, 0x650,
    0xaf0, 0xbf9, 0x8f3, 0x9fa, 0xef6, 0xfff, 0xcf5, 0xdfc,
    0x2fc, 0x3f5, 0xff, 0x1f6, 0x6fa, 0x7f3, 0x4f9, 0x5f0,
    0xb60, 0xa69, 0x963, 0x86a, 0xf66, 0xe6f, 0xd65, 0xc6c,
    0x36c, 0x265, 0x16f, 0x66, 0x76a, 0x663, 0x569, 0x460,
    0xca0, 0xda9, 0xea3, 0xfaa, 0x8a6, 0x9af, 0xaa5, 0xbac,
    0x4ac, 0x5a5, 0x6af, 0x7a6, 0xaa, 0x1a3, 0x2a9, 0x3a0,
    0xd30, 0xc39, 0xf33, 0xe3a, 0x936, 0x83f, 0xb35, 0xa3c,
    0x53c, 0x435, 0x73f, 0x636, 0x13a, 0x33, 0x339, 0x230,
    0xe90, 0xf99, 0xc93, 0xd9a, 0xa96, 0xb9f, 0x895, 0x99c,
    0x69c, 0x795, 0x49f, 0x596, 0x29a, 0x393, 0x99, 0x190,
    0xf00, 0xe09, 0xd03, 0xc0a, 0xb06, 0xa0f, 0x905, 0x80c,
    0x70c, 0x605, 0x50f, 0x406, 0x30a, 0x203, 0x109, 0x0
]

TRI_TABLE = [
    [], [0, 8, 3], [0, 1, 9], [1, 8, 3, 9, 8, 1], [1, 2, 10], [0, 8, 3, 1, 2, 10],
    [9, 2, 10, 0, 2, 9], [2, 8, 3, 2, 10, 8, 10, 9, 8], [3, 11, 2], [0, 11, 2, 8, 11, 0],
    [1, 9, 0, 2, 3, 11], [1, 11, 2, 1, 9, 11, 9, 8, 11], [3, 10, 1, 11, 10, 3],
    [0, 10, 1, 0, 8, 10, 8, 11, 10], [3, 9, 0, 3, 11, 9, 11, 10, 9],
    [9, 8, 10, 10, 8, 11], [4, 7, 8], [4, 3, 0, 7, 3, 4], [0, 1, 9, 8, 4, 7],
    [4, 1, 9, 4, 7, 1, 7, 3, 1], [1, 2, 10, 8, 4, 7], [3, 4, 7, 3, 0, 4, 1, 2, 10],
    [9, 2, 10, 9, 0, 2, 8, 4, 7], [2, 10, 9, 2, 9, 7, 2, 7, 3, 7, 9, 4],
    [8, 4, 7, 3, 11, 2], [11, 4, 7, 11, 2, 4, 2, 0, 4], [9, 0, 1, 8, 4, 7, 2, 3, 11],
    [4, 7, 11, 9, 4, 11, 9, 11, 2, 9, 2, 1], [3, 10, 1, 3, 11, 10, 7, 8, 4],
    [1, 11, 10, 1, 4, 11, 1, 0, 4, 7, 11, 4], [4, 7, 8, 9, 0, 11, 9, 11, 10, 11, 0, 3],
    [4, 7, 11, 4, 11, 9, 9, 11, 10], [9, 5, 4], [9, 5, 4, 0, 8, 3],
    [0, 5, 4, 1, 5, 0], [8, 5, 4, 8, 3, 5, 3, 1, 5], [1, 2, 10, 9, 5, 4],
    [3, 0, 8, 1, 2, 10, 4, 9, 5], [5, 2, 10, 5, 4, 2, 4, 0, 2],
    [2, 10, 5, 3, 2, 5, 3, 5, 4, 3, 4, 8], [9, 5, 4, 2, 3, 11],
    [0, 11, 2, 0, 8, 11, 4, 9, 5], [0, 5, 4, 0, 1, 5, 2, 3, 11],
    [2, 1, 5, 2, 5, 8, 2, 8, 11, 4, 8, 5], [10, 3, 11, 10, 1, 3, 9, 5, 4],
    [4, 9, 5, 0, 8, 1, 8, 10, 1, 8, 11, 10], [5, 4, 0, 5, 0, 11, 5, 11, 10, 11, 0, 3],
    [5, 4, 8, 5, 8, 10, 10, 8, 11], [9, 7, 8, 5, 7, 9], [9, 3, 0, 9, 5, 3, 5, 7, 3],
    [0, 7, 8, 0, 1, 7, 1, 5, 7], [1, 5, 3, 3, 5, 7], [9, 7, 8, 9, 5, 7, 10, 1, 2],
    [10, 1, 2, 9, 5, 0, 5, 3, 0, 5, 7, 3], [8, 0, 2, 8, 2, 5, 8, 5, 7, 10, 5, 2],
    [2, 10, 5, 2, 5, 3, 3, 5, 7], [7, 9, 5, 7, 8, 9, 3, 11, 2],
    [9, 5, 7, 9, 7, 2, 9, 2, 0, 2, 7, 11], [2, 3, 11, 0, 1, 8, 1, 7, 8, 1, 5, 7],
    [11, 2, 1, 11, 1, 7, 7, 1, 5], [9, 5, 8, 8, 5, 7, 10, 1, 3, 10, 3, 11],
    [5, 7, 0, 5, 0, 9, 7, 11, 0, 1, 0, 10, 11, 10, 0],
    [11, 10, 0, 11, 0, 3, 10, 5, 0, 8, 0, 7, 5, 7, 0],
    [11, 10, 5, 7, 11, 5], [10, 6, 5], [0, 8, 3, 5, 10, 6],
    [9, 0, 1, 5, 10, 6], [1, 8, 3, 1, 9, 8, 5, 10, 6], [1, 6, 5, 2, 6, 1],
    [1, 6, 5, 1, 2, 6, 3, 0, 8], [9, 6, 5, 9, 0, 6, 0, 2, 6],
    [5, 9, 8, 5, 8, 2, 5, 2, 6, 3, 2, 8], [2, 3, 11, 10, 6, 5],
    [11, 0, 8, 11, 2, 0, 10, 6, 5], [0, 1, 9, 2, 3, 11, 5, 10, 6],
    [5, 10, 6, 1, 9, 2, 9, 11, 2, 9, 8, 11], [6, 3, 11, 6, 5, 3, 5, 1, 3],
    [0, 8, 11, 0, 11, 5, 0, 5, 1, 5, 11, 6], [3, 11, 6, 0, 3, 6, 0, 6, 5, 0, 5, 9],
    [6, 5, 9, 6, 9, 11, 11, 9, 8], [5, 10, 6, 4, 7, 8],
    [4, 3, 0, 4, 7, 3, 6, 5, 10], [1, 9, 0, 5, 10, 6, 8, 4, 7],
    [10, 6, 5, 1, 9, 7, 1, 7, 3, 7, 9, 4], [6, 1, 2, 6, 5, 1, 4, 7, 8],
    [1, 2, 5, 5, 2, 6, 3, 0, 4, 3, 4, 7], [8, 4, 7, 9, 0, 5, 0, 6, 5, 0, 2, 6],
    [7, 3, 9, 7, 9, 4, 3, 2, 9, 5, 9, 6, 2, 6, 9], [3, 11, 2, 7, 8, 4, 10, 6, 5],
    [5, 10, 6, 4, 7, 2, 4, 2, 0, 2, 7, 11], [0, 1, 9, 4, 7, 8, 2, 3, 11, 5, 10, 6],
    [9, 2, 1, 9, 11, 2, 9, 4, 11, 7, 11, 4, 5, 10, 6],
    [8, 4, 7, 3, 11, 5, 3, 5, 1, 5, 11, 6], [5, 1, 11, 5, 11, 6, 1, 0, 11, 7, 11, 4, 0, 4, 11],
    [0, 5, 9, 0, 6, 5, 0, 3, 6, 11, 6, 3, 8, 4, 7],
    [6, 5, 9, 6, 9, 11, 4, 7, 9, 7, 11, 9], [10, 4, 9, 6, 4, 10],
    [4, 10, 6, 4, 9, 10, 0, 8, 3], [10, 0, 1, 10, 6, 0, 6, 4, 0],
    [8, 3, 1, 8, 1, 6, 8, 6, 4, 6, 1, 10], [1, 4, 9, 1, 2, 4, 2, 6, 4],
    [3, 0, 8, 1, 2, 9, 2, 4, 9, 2, 6, 4], [0, 2, 4, 4, 2, 6], [8, 3, 2, 8, 2, 4, 4, 2, 6],
    [10, 4, 9, 10, 6, 4, 11, 2, 3], [0, 8, 2, 2, 8, 11, 4, 9, 10, 4, 10, 6],
    [3, 11, 2, 0, 1, 6, 0, 6, 4, 6, 1, 10], [6, 4, 1, 6, 1, 10, 4, 8, 1, 2, 1, 11, 8, 11, 1],
    [9, 6, 4, 9, 3, 6, 9, 1, 3, 11, 6, 3], [8, 11, 1, 8, 1, 0, 11, 6, 1, 9, 1, 4, 6, 4, 1],
    [3, 11, 6, 3, 6, 0, 0, 6, 4], [6, 4, 8, 11, 6, 8], [7, 10, 6, 7, 8, 10, 8, 9, 10],
    [0, 7, 3, 0, 10, 7, 0, 9, 10, 6, 7, 10], [10, 6, 7, 1, 10, 7, 1, 7, 8, 1, 8, 0],
    [10, 6, 7, 10, 7, 1, 1, 7, 3], [1, 2, 6, 1, 6, 8, 1, 8, 9, 8, 6, 7],
    [2, 6, 9, 2, 9, 1, 6, 7, 9, 0, 9, 3, 7, 3, 9], [7, 8, 0, 7, 0, 6, 6, 0, 2],
    [7, 3, 2, 6, 7, 2], [2, 3, 11, 10, 6, 8, 10, 8, 9, 8, 6, 7],
    [2, 0, 7, 2, 7, 11, 0, 9, 7, 6, 7, 10, 9, 10, 7],
    [1, 8, 0, 1, 7, 8, 1, 10, 7, 6, 7, 10, 2, 3, 11],
    [11, 2, 1, 11, 1, 7, 10, 6, 1, 6, 7, 1], [8, 9, 6, 8, 6, 7, 9, 1, 6, 11, 6, 3, 1, 3, 6],
    [0, 9, 1, 11, 6, 7], [7, 8, 0, 7, 0, 6, 3, 11, 0, 11, 6, 0], [7, 11, 6],
    [7, 6, 11], [3, 0, 8, 11, 7, 6], [0, 1, 9, 11, 7, 6], [8, 1, 9, 8, 3, 1, 11, 7, 6],
    [10, 1, 2, 6, 11, 7], [1, 2, 10, 3, 0, 8, 6, 11, 7], [2, 9, 0, 2, 10, 9, 6, 11, 7],
    [6, 11, 7, 2, 10, 3, 10, 8, 3, 10, 9, 8], [7, 2, 3, 6, 2, 7],
    [7, 0, 8, 7, 6, 0, 6, 2, 0], [2, 7, 6, 2, 3, 7, 0, 1, 9],
    [1, 6, 2, 1, 8, 6, 1, 9, 8, 8, 7, 6], [10, 7, 6, 10, 1, 7, 1, 3, 7],
    [10, 7, 6, 1, 7, 10, 1, 8, 7, 1, 0, 8], [0, 3, 7, 0, 7, 10, 0, 10, 9, 6, 10, 7],
    [7, 6, 10, 7, 10, 8, 8, 10, 9], [6, 8, 4, 11, 8, 6], [3, 6, 11, 3, 0, 6, 0, 4, 6],
    [8, 6, 11, 8, 4, 6, 9, 0, 1], [9, 4, 6, 9, 6, 3, 9, 3, 1, 11, 3, 6],
    [6, 8, 4, 6, 11, 8, 2, 10, 1], [1, 2, 10, 3, 0, 11, 0, 6, 11, 0, 4, 6],
    [4, 11, 8, 4, 6, 11, 0, 2, 9, 2, 10, 9], [10, 9, 3, 10, 3, 2, 9, 4, 3, 11, 3, 6, 4, 6, 3],
    [8, 2, 3, 8, 4, 2, 4, 6, 2], [0, 4, 2, 4, 6, 2], [1, 9, 0, 2, 3, 4, 2, 4, 6, 4, 3, 8],
    [1, 9, 4, 1, 4, 2, 2, 4, 6], [8, 1, 3, 8, 6, 1, 8, 4, 6, 6, 10, 1],
    [10, 1, 0, 10, 0, 6, 6, 0, 4], [4, 6, 3, 4, 3, 8, 6, 10, 3, 0, 3, 9, 10, 9, 3],
    [10, 9, 4, 6, 10, 4], [4, 9, 5, 7, 6, 11], [0, 8, 3, 4, 9, 5, 11, 7, 6],
    [5, 0, 1, 5, 4, 0, 7, 6, 11], [11, 7, 6, 8, 3, 4, 3, 5, 4, 3, 1, 5],
    [9, 5, 4, 10, 1, 2, 7, 6, 11], [6, 11, 7, 1, 2, 10, 0, 8, 3, 4, 9, 5],
    [7, 6, 11, 5, 4, 10, 4, 2, 10, 4, 0, 2], [3, 4, 8, 3, 5, 4, 3, 2, 5, 10, 5, 2, 11, 7, 6],
    [7, 2, 3, 7, 6, 2, 5, 4, 9], [9, 5, 4, 0, 8, 6, 0, 6, 2, 6, 8, 7],
    [3, 6, 2, 3, 7, 6, 1, 5, 0, 5, 4, 0], [6, 2, 8, 6, 8, 7, 2, 1, 8, 4, 8, 5, 1, 5, 8],
    [9, 5, 4, 10, 1, 6, 1, 7, 6, 1, 3, 7], [1, 6, 10, 1, 7, 6, 1, 0, 7, 8, 7, 0, 9, 5, 4],
    [4, 0, 10, 4, 10, 5, 0, 3, 10, 6, 10, 7, 3, 7, 10], [7, 6, 10, 7, 10, 8, 5, 4, 10, 4, 8, 10],
    [6, 9, 5, 6, 11, 9, 11, 8, 9], [3, 6, 11, 0, 6, 3, 0, 5, 6, 0, 9, 5],
    [0, 11, 8, 0, 5, 11, 0, 1, 5, 5, 6, 11], [6, 11, 3, 6, 3, 5, 5, 3, 1],
    [1, 2, 10, 9, 5, 11, 9, 11, 8, 11, 5, 6], [0, 11, 3, 0, 6, 11, 0, 9, 6, 5, 6, 9, 1, 2, 10],
    [11, 8, 5, 11, 5, 6, 8, 0, 5, 10, 5, 2, 0, 2, 5], [6, 11, 3, 6, 3, 5, 2, 10, 3, 10, 5, 3],
    [5, 8, 9, 5, 2, 8, 5, 6, 2, 3, 8, 2], [9, 5, 6, 9, 6, 0, 0, 6, 2],
    [1, 5, 8, 1, 8, 0, 5, 6, 8, 3, 8, 2, 6, 2, 8], [1, 5, 6, 2, 1, 6],
    [1, 3, 6, 1, 6, 10, 3, 8, 6, 5, 6, 9, 8, 9, 6], [10, 1, 0, 10, 0, 6, 9, 5, 0, 5, 6, 0],
    [0, 3, 8, 5, 6, 10], [10, 5, 6], [11, 5, 10, 7, 5, 11], [11, 5, 10, 11, 7, 5, 8, 3, 0],
    [5, 11, 7, 5, 10, 11, 1, 9, 0], [10, 7, 5, 10, 11, 7, 9, 8, 1, 8, 3, 1],
    [11, 1, 2, 11, 7, 1, 7, 5, 1], [0, 8, 3, 1, 2, 7, 1, 7, 5, 7, 2, 11],
    [9, 7, 5, 9, 2, 7, 9, 0, 2, 2, 11, 7], [7, 5, 2, 7, 2, 11, 5, 9, 2, 3, 2, 8, 9, 8, 2],
    [2, 5, 10, 2, 3, 5, 3, 7, 5], [8, 2, 0, 8, 5, 2, 8, 7, 5, 10, 2, 5],
    [9, 0, 1, 5, 10, 3, 5, 3, 7, 3, 10, 2], [9, 8, 2, 9, 2, 1, 8, 7, 2, 10, 2, 5, 7, 5, 2],
    [1, 3, 5, 3, 7, 5], [0, 8, 7, 0, 7, 1, 1, 7, 5], [9, 0, 3, 9, 3, 5, 5, 3, 7],
    [9, 8, 7, 5, 9, 7], [5, 8, 4, 5, 10, 8, 10, 11, 8], [5, 0, 4, 5, 11, 0, 5, 10, 11, 11, 3, 0],
    [0, 1, 9, 8, 4, 10, 8, 10, 11, 10, 4, 5], [10, 11, 4, 10, 4, 5, 11, 3, 4, 9, 4, 1, 3, 1, 4],
    [2, 5, 1, 2, 8, 5, 2, 11, 8, 4, 5, 8], [0, 4, 11, 0, 11, 3, 4, 5, 11, 2, 11, 1, 5, 1, 11],
    [0, 2, 5, 0, 5, 9, 2, 11, 5, 4, 5, 8, 11, 8, 5], [9, 4, 5, 2, 11, 3],
    [2, 5, 10, 3, 5, 2, 3, 4, 5, 3, 8, 4], [5, 10, 2, 5, 2, 4, 4, 2, 0],
    [3, 10, 2, 3, 5, 10, 3, 8, 5, 4, 5, 8, 0, 1, 9], [5, 10, 2, 5, 2, 4, 1, 9, 2, 9, 4, 2],
    [8, 4, 5, 8, 5, 3, 3, 5, 1], [0, 4, 5, 1, 0, 5], [8, 4, 5, 8, 5, 3, 9, 0, 5, 0, 3, 5],
    [9, 4, 5], [4, 11, 7, 4, 9, 11, 9, 10, 11], [0, 8, 3, 4, 9, 7, 9, 11, 7, 9, 10, 11],
    [1, 10, 11, 1, 11, 4, 1, 4, 0, 7, 4, 11], [3, 1, 4, 3, 4, 8, 1, 10, 4, 7, 4, 11, 10, 11, 4],
    [4, 11, 7, 9, 11, 4, 9, 2, 11, 9, 1, 2], [9, 7, 4, 9, 11, 7, 9, 1, 11, 2, 11, 1, 0, 8, 3],
    [11, 7, 4, 11, 4, 2, 2, 4, 0], [11, 7, 4, 11, 4, 2, 8, 3, 4, 3, 2, 4],
    [2, 9, 10, 2, 7, 9, 2, 3, 7, 7, 4, 9], [9, 10, 7, 9, 7, 4, 10, 2, 7, 8, 7, 0, 2, 0, 7],
    [3, 7, 10, 3, 10, 2, 7, 4, 10, 1, 10, 0, 4, 0, 10], [1, 10, 2, 8, 7, 4],
    [4, 9, 1, 4, 1, 7, 7, 1, 3], [4, 9, 1, 4, 1, 7, 0, 8, 1, 8, 7, 1], [4, 0, 3, 7, 4, 3],
    [4, 8, 7], [9, 10, 8, 10, 11, 8], [3, 0, 9, 3, 9, 11, 11, 9, 10],
    [0, 1, 10, 0, 10, 8, 8, 10, 11], [3, 1, 10, 11, 3, 10], [1, 2, 11, 1, 11, 9, 9, 11, 8],
    [3, 0, 9, 3, 9, 11, 1, 2, 9, 2, 11, 9], [0, 2, 11, 8, 0, 11], [3, 2, 11], [2, 3, 8, 2, 8, 10, 10, 8, 9],
    [9, 10, 2, 0, 9, 2], [2, 3, 8, 2, 8, 10, 0, 1, 8, 1, 10, 8], [1, 10, 2], [1, 3, 8, 9, 1, 8],
    [0, 9, 1], [0, 3, 8], []
]


def field_value(x, y, z, balls):
    """Campo metaball optimizado"""
    s = 0.0
    for b in balls:
        dx = x - b["x"]
        dy = y - b["y"]
        dz = z - b["z"]
        d2 = dx*dx + dy*dy + dz*dz + 1e-9
        r2 = b["r"] * b["r"]
        inf = b.get("influence", 1.0)
        s += (r2 / d2) * inf
    return s


def lerp_vertex(p1, v1, p2, v2, iso):
    if abs(v2 - v1) < 1e-9:
        return tuple((p1[i] + p2[i]) * 0.5 for i in range(3))
    t = (iso - v1) / (v2 - v1)
    return tuple(p1[i] + t * (p2[i] - p1[i]) for i in range(3))


def compute_normal(a, b, c):
    ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
    vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
    nx, ny, nz = uy*vz - uz*vy, uz*vx - ux*vz, ux*vy - uy*vx
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 1e-9:
        return (nx/length, ny/length, nz/length)
    return (0, 0, 1)


def marching_cubes(balls, iso, resolution):
    """Marching Cubes COMPLETO"""
    if not balls:
        return []

    max_r = max(b["r"] for b in balls)
    margin = max_r * 3.0

    xs = [b["x"] for b in balls]
    ys = [b["y"] for b in balls]
    zs = [b["z"] for b in balls]

    minx, maxx = min(xs) - margin, max(xs) + margin
    miny, maxy = min(ys) - margin, max(ys) + margin
    minz, maxz = min(zs) - margin, max(zs) + margin

    size = max(maxx-minx, maxy-miny, maxz-minz)
    n = max(10, int(resolution))
    step = size / n

    nx = max(2, int((maxx-minx)/step))
    ny = max(2, int((maxy-miny)/step))
    nz = max(2, int((maxz-minz)/step))

    triangles = []

    # Cache de valores
    grid = {}

    def get_value(ix, iy, iz):
        key = (ix, iy, iz)
        if key not in grid:
            x = minx + ix * step
            y = miny + iy * step
            z = minz + iz * step
            grid[key] = field_value(x, y, z, balls)
        return grid[key]

    for ix in range(nx):
        for iy in range(ny):
            for iz in range(nz):
                # 8 esquinas del cubo
                v = [get_value(ix+i, iy+j, iz+k) 
                     for k in range(2) for j in range(2) for i in range(2)]
                
                # Calcular índice del cubo
                cubeindex = 0
                for i in range(8):
                    if v[i] < iso:
                        cubeindex |= (1 << i)
                
                if cubeindex == 0 or cubeindex == 255:
                    continue
                
                # Posiciones de las esquinas
                p = [(minx + (ix+i)*step, miny + (iy+j)*step, minz + (iz+k)*step)
                     for k in range(2) for j in range(2) for i in range(2)]
                
                # Interpolación en aristas
                edge_list = EDGE_TABLE[cubeindex]
                if edge_list == 0:
                    continue
                
                vert_list = []
                edge_connections = [
                    (0,1), (1,2), (2,3), (3,0),
                    (4,5), (5,6), (6,7), (7,4),
                    (0,4), (1,5), (2,6), (3,7)
                ]
                
                for i, (i1, i2) in enumerate(edge_connections):
                    if edge_list & (1 << i):
                        vert_list.append(lerp_vertex(p[i1], v[i1], p[i2], v[i2], iso))
                
                # Generar triángulos
                tri_list = TRI_TABLE[cubeindex]
                for i in range(0, len(tri_list), 3):
                    if i+2 < len(tri_list):
                        t1, t2, t3 = tri_list[i], tri_list[i+1], tri_list[i+2]
                        if t1 < len(vert_list) and t2 < len(vert_list) and t3 < len(vert_list):
                            triangles.append((vert_list[t1], vert_list[t2], vert_list[t3]))

    return triangles


def write_stl(path, triangles):
    with open(path, "wb") as f:
        f.write(b"Metaballs"[:80].ljust(80, b" "))
        f.write(struct.pack("<I", len(triangles)))
        for tri in triangles:
            n = compute_normal(*tri)
            f.write(struct.pack("<3f", *n))
            for v in tri:
                f.write(struct.pack("<3f", *v))
            f.write(struct.pack("<H", 0))


# ============= FUSION 360 INTEGRATION =============

def get_app_ui():
    return adsk.core.Application.get(), adsk.core.Application.get().userInterface


def get_design():
    app, _ = get_app_ui()
    prod = app.activeProduct
    return adsk.fusion.Design.cast(prod) if prod else None


def is_metaball(body):
    try:
        return body and body.attributes.itemByName(ATTR_GROUP, ATTR_METABALL) is not None
    except:
        return False


def get_family(body):
    try:
        attr = body.attributes.itemByName(ATTR_GROUP, ATTR_FAMILY)
        return attr.value if attr else "A"
    except:
        return "A"


def get_influence(body):
    try:
        attr = body.attributes.itemByName(ATTR_GROUP, ATTR_INFLUENCE)
        return float(attr.value) if attr else 1.0
    except:
        return 1.0


def collect_metaballs(root, family="A"):
    """Recolecta TODAS las metaballs de una familia"""
    balls = []
    
    def scan(comp):
        try:
            for i in range(comp.bRepBodies.count):
                body = comp.bRepBodies.item(i)
                if is_metaball(body) and get_family(body) == family:
                    bb = body.boundingBox
                    cx = (bb.minPoint.x + bb.maxPoint.x) / 2
                    cy = (bb.minPoint.y + bb.maxPoint.y) / 2
                    cz = (bb.minPoint.z + bb.maxPoint.z) / 2
                    r = max(bb.maxPoint.x - bb.minPoint.x,
                           bb.maxPoint.y - bb.minPoint.y,
                           bb.maxPoint.z - bb.minPoint.z) / 2
                    balls.append({
                        "x": cx, "y": cy, "z": cz, "r": r,
                        "influence": get_influence(body),
                        "body": body
                    })
            
            for j in range(comp.occurrences.count):
                occ = comp.occurrences.item(j)
                if occ and occ.component:
                    scan(occ.component)
        except:
            pass
    
    scan(root)
    return balls


def find_preview_comp(root):
    """Encuentra el componente de preview"""
    try:
        for i in range(root.occurrences.count):
            occ = root.occurrences.item(i)
            if occ and occ.component:
                attr = occ.component.attributes.itemByName(ATTR_GROUP, "preview")
                if attr:
                    return occ, occ.component
    except:
        pass
    return None, None


def ensure_preview_comp(root):
    occ, comp = find_preview_comp(root)
    if comp:
        return occ, comp
    
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = "Metaballs_Preview"
    comp.attributes.add(ATTR_GROUP, "preview", "true")
    return occ, comp


def clear_preview(comp):
    try:
        for i in range(comp.meshBodies.count -1, -1, -1):
            comp.meshBodies.item(i).deleteMe()
        for i in range(comp.features.baseFeatures.count - 1, -1, -1):
            comp.features.baseFeatures.item(i).deleteMe()
    except:
        pass


def import_mesh(comp, stl_path):
    try:
        bf = comp.features.baseFeatures.add()
        bf.startEdit()
        comp.meshBodies.add(stl_path, adsk.fusion.MeshUnits.CentimeterMeshUnit)
        bf.finishEdit()
        
        if comp.meshBodies.count > 0:
            mb = comp.meshBodies.item(comp.meshBodies.count - 1)
            mb.name = "Metaballs"
            mb.opacity = 0.6
            return mb
    except:
        pass
    return None


def update_preview(family="A"):
    """Actualiza el preview de metaballs"""
    try:
        design = get_design()
        if not design:
            return False
        
        root = design.rootComponent
        balls = collect_metaballs(root, family)
        
        occ, comp = ensure_preview_comp(root)
        clear_preview(comp)
        
        if not balls:
            return True
        
        tris = marching_cubes(balls, _settings["iso"], _settings["resolution"])
        
        if not tris:
            return False
        
        stl_path = os.path.join(tempfile.gettempdir(), f"mb_{family}_{time.time()}.stl")
        write_stl(stl_path, tris)
        
        import_mesh(comp, stl_path)
        
        try:
            os.remove(stl_path)
        except:
            pass
        
        return True
    except:
        return False


# ============= MONITORING THREAD =============

def monitor_changes():
    """Thread que monitorea cambios en metaballs"""
    global _monitoring
    last_check = {}
    
    while _monitoring:
        try:
            if _settings["auto_update"]:
                design = get_design()
                if design:
                    root = design.rootComponent
                    current_state = {}
                    
                    def check_comp(comp):
                        for i in range(comp.bRepBodies.count):
                            body = comp.bRepBodies.item(i)
                            if is_metaball(body):
                                fam = get_family(body)
                                bb = body.boundingBox
                                key = f"{fam}_{body.entityToken}"
                                state = (bb.minPoint.asArray(), bb.maxPoint.asArray())
                                current_state[key] = state
                        
                        for j in range(comp.occurrences.count):
                            occ = comp.occurrences.item(j)
                            if occ and occ.component:
                                check_comp(occ.component)
                    
                    check_comp(root)
                    
                    if current_state != last_check:
                        families = set(k.split('_')[0] for k in current_state.keys())
                        for fam in families:
                            update_preview(fam)
                        last_check = current_state.copy()
                        
        except:
            pass
        
        time.sleep(_settings["update_delay"])


# ============= COMMANDS =============

class AddMetaballHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            app, ui = get_app_ui()
            design = get_design()
            if not design:
                return

            inputs = args.command.commandInputs
            rad = inputs.itemById('radius').value
            fam = inputs.itemById('family').value.strip() or "A"
            inf = inputs.itemById('influence').value

            root = design.rootComponent
            
            # Crear esfera
            comp = root.occurrences.addNewComponent(adsk.core.Matrix3D.create()).component
            sketch = comp.sketches.add(comp.xYConstructionPlane)
            circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
                adsk.core.Point3D.create(0, 0, 0), rad)
            
            prof = sketch.profiles.item(0)
            ext = comp.features.extrudeFeatures.createInput(
                prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            ext.setDistanceExtent(False, adsk.core.ValueInput.createByReal(rad * 2))
            ext.startExtent = adsk.fusion.OffsetStartDefinition.create(
                adsk.core.ValueInput.createByReal(-rad))
            
            feat = comp.features.extrudeFeatures.add(ext)
            
            if feat.bodies.count > 0:
                body = feat.bodies.item(0)
                body.name = f"MB_{fam}"
                body.opacity = 0.25
                body.attributes.add(ATTR_GROUP, ATTR_METABALL, "true")
                body.attributes.add(ATTR_GROUP, ATTR_FAMILY, fam)
                body.attributes.add(ATTR_GROUP, ATTR_INFLUENCE, str(inf))
            
            if _settings["auto_update"]:
                update_preview(fam)

        except:
            pass


class AddMetaballCreated(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        cmd = args.command
        inputs = cmd.commandInputs
        
        inputs.addValueInput('radius', 'Radio', 'cm', adsk.core.ValueInput.createByReal(3.0))
        inputs.addStringValueInput('family', 'Familia', 'A')
        inputs.addValueInput('influence', 'Influencia', '', adsk.core.ValueInput.createByReal(1.0))
        
        handler = AddMetaballHandler()
        cmd.execute.add(handler)
        _handlers.append(handler)


class SettingsHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            inputs = args.command.commandInputs
            
            _settings["iso"] = inputs.itemById('iso').value
            _settings["resolution"] = inputs.itemById('resolution').value
            _settings["auto_update"] = inputs.itemById('auto').value
            
            fam = inputs.itemById('family').value.strip() or "A"
            update_preview(fam)
        except:
            pass


class SettingsCreated(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        cmd = args.command
        inputs = cmd.commandInputs
        
        inputs.addStringValueInput('family', 'Familia', 'A')
        inputs.addValueInput('iso', 'Threshold', '', 
                           adsk.core.ValueInput.createByReal(_settings["iso"]))
        inputs.addIntegerSpinnerCommandInput('resolution', 'Resolución', 
                                            10, 100, 1, _settings["resolution"])
        inputs.addBoolValueInput('auto', 'Auto-actualizar', True, '', 
                                _settings["auto_update"])
        
        handler = SettingsHandler()
        cmd.execute.add(handler)
        _handlers.append(handler)


class DeleteHandler(adsk.core.CommandEventHandler):
    def notify(self, args):
        try:
            app, ui = get_app_ui()
            sels = ui.activeSelections
            
            if sels.count == 0:
                return
            
            families = set()
            
            for i in range(sels.count):
                entity = sels.item(i).entity
                body = entity if isinstance(entity, adsk.fusion.BRepBody) else getattr(entity, 'body', None)
                
                if body and is_metaball(body):
                    families.add(get_family(body))
                    body.deleteMe()
            
            for fam in families:
                update_preview(fam)
        except:
            pass


class DeleteCreated(adsk.core.CommandCreatedEventHandler):
    def notify(self, args):
        handler = DeleteHandler()
        args.command.execute.add(handler)
        _handlers.append(handler)


def add_button(ui, id, name, desc, handler, panel):
    cmd_def = ui.commandDefinitions.itemById(id)
    if not cmd_def:
        cmd_def = ui.commandDefinitions.addButtonDefinition(id, name, desc, "")
    
    cmd_def.commandCreated.add(handler)
    _handlers.append(handler)
    
    if not panel.controls.itemById(id):
        panel.controls.addCommand(cmd_def).isPromoted = True


def run(context):
    global _monitoring, _monitor_thread
    
    try:
        app, ui = get_app_ui()
        workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
        if not workspace:
            return
        
        panel = workspace.toolbarPanels.itemById(config.PANEL_ID)
        if not panel:
            return
        
        add_button(ui, CMD_ID_ADD, "Add Metaball", "Añade metaball", 
                  AddMetaballCreated(), panel)
        add_button(ui, CMD_ID_SETTINGS, "Settings", "Configura metaballs",
                  SettingsCreated(), panel)
        add_button(ui, CMD_ID_DELETE, "Delete", "Elimina metaballs",
                  DeleteCreated(), panel)
        
        # Iniciar monitoring
        _monitoring = True
        _monitor_thread = threading.Thread(target=monitor_changes, daemon=True)
        _monitor_thread.start()
        
    except:
        pass


def stop(context):
    global _monitoring, _monitor_thread
    
    _monitoring = False
    if _monitor_thread:
        _monitor_thread.join(timeout=1.0)
    
    try:
        app, ui = get_app_ui()
        workspace = ui.workspaces.itemById(config.WORKSPACE_ID)
        if not workspace:
            return
        
        panel = workspace.toolbarPanels.itemById(config.PANEL_ID)
        if not panel:
            return
        
        for cid in [CMD_ID_ADD, CMD_ID_SETTINGS, CMD_ID_DELETE]:
            ctrl = panel.controls.itemById(cid)
            if ctrl:
                ctrl.deleteMe()
            
            cmd_def = ui.commandDefinitions.itemById(cid)
            if cmd_def:
                cmd_def.deleteMe()
        
        _handlers.clear()
    except:
        pass
