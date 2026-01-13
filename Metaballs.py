#Author-Maurichilean3d
#Description-Create organic metaballs shapes in Fusion 360

import adsk.core, adsk.fusion, adsk.cam, traceback
import math
import os

# Global variables
_app = None
_ui = None
_handlers = []
_cmdDef = None

# Command identity
CMD_ID = 'MetaballsAddon'
CMD_NAME = 'Metaballs'
CMD_DESCRIPTION = 'Create organic metaballs shapes'
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'

# Marching Cubes lookup tables
edgeTable = [
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

triTable = [
    [], [0, 8, 3], [0, 1, 9], [1, 8, 3, 9, 8, 1], [1, 2, 10], [0, 8, 3, 1, 2, 10],
    [9, 2, 10, 0, 2, 9], [2, 8, 3, 2, 10, 8, 10, 9, 8], [3, 11, 2], [0, 11, 2, 8, 11, 0],
    [1, 9, 0, 2, 3, 11], [1, 11, 2, 1, 9, 11, 9, 8, 11], [3, 10, 1, 11, 10, 3],
    [0, 10, 1, 0, 8, 10, 8, 11, 10], [3, 9, 0, 3, 11, 9, 11, 10, 9], [9, 8, 10, 10, 8, 11],
    [4, 7, 8], [4, 3, 0, 7, 3, 4], [0, 1, 9, 8, 4, 7], [4, 1, 9, 4, 7, 1, 7, 3, 1],
    [1, 2, 10, 8, 4, 7], [3, 4, 7, 3, 0, 4, 1, 2, 10], [9, 2, 10, 9, 0, 2, 8, 4, 7],
    [2, 10, 9, 2, 9, 7, 2, 7, 3, 7, 9, 4], [8, 4, 7, 3, 11, 2], [11, 4, 7, 11, 2, 4, 2, 0, 4],
    [9, 0, 1, 8, 4, 7, 2, 3, 11], [4, 7, 11, 9, 4, 11, 9, 11, 2, 9, 2, 1],
    [3, 10, 1, 3, 11, 10, 7, 8, 4], [1, 11, 10, 1, 4, 11, 1, 0, 4, 7, 11, 4],
    [4, 7, 8, 9, 0, 11, 9, 11, 10, 11, 0, 3], [4, 7, 11, 4, 11, 9, 9, 11, 10],
    [9, 5, 4], [9, 5, 4, 0, 8, 3], [0, 5, 4, 1, 5, 0], [8, 5, 4, 8, 3, 5, 3, 1, 5],
    [1, 2, 10, 9, 5, 4], [3, 0, 8, 1, 2, 10, 4, 9, 5], [5, 2, 10, 5, 4, 2, 4, 0, 2],
    [2, 10, 5, 3, 2, 5, 3, 5, 4, 3, 4, 8], [9, 5, 4, 2, 3, 11], [0, 11, 2, 0, 8, 11, 4, 9, 5],
    [0, 5, 4, 0, 1, 5, 2, 3, 11], [2, 1, 5, 2, 5, 8, 2, 8, 11, 4, 8, 5],
    [10, 3, 11, 10, 1, 3, 9, 5, 4], [4, 9, 5, 0, 8, 1, 8, 10, 1, 8, 11, 10],
    [5, 4, 0, 5, 0, 11, 5, 11, 10, 11, 0, 3], [5, 4, 8, 5, 8, 10, 10, 8, 11],
    [9, 7, 8, 5, 7, 9], [9, 3, 0, 9, 5, 3, 5, 7, 3], [0, 7, 8, 0, 1, 7, 1, 5, 7],
    [1, 5, 3, 3, 5, 7], [9, 7, 8, 9, 5, 7, 10, 1, 2], [10, 1, 2, 9, 5, 0, 5, 3, 0, 5, 7, 3],
    [8, 0, 2, 8, 2, 5, 8, 5, 7, 10, 5, 2], [2, 10, 5, 2, 5, 3, 3, 5, 7],
    [7, 9, 5, 7, 8, 9, 3, 11, 2], [9, 5, 7, 9, 7, 2, 9, 2, 0, 2, 7, 11],
    [2, 3, 11, 0, 1, 8, 1, 7, 8, 1, 5, 7], [11, 2, 1, 11, 1, 7, 7, 1, 5],
    [9, 5, 8, 8, 5, 7, 10, 1, 3, 10, 3, 11], [5, 7, 0, 5, 0, 9, 7, 11, 0, 1, 0, 10, 11, 10, 0],
    [11, 10, 0, 11, 0, 3, 10, 5, 0, 8, 0, 7, 5, 7, 0], [11, 10, 5, 7, 11, 5],
    [10, 6, 5], [0, 8, 3, 5, 10, 6], [9, 0, 1, 5, 10, 6], [1, 8, 3, 1, 9, 8, 5, 10, 6],
    [1, 6, 5, 2, 6, 1], [1, 6, 5, 1, 2, 6, 3, 0, 8], [9, 6, 5, 9, 0, 6, 0, 2, 6],
    [5, 9, 8, 5, 8, 2, 5, 2, 6, 3, 2, 8], [2, 3, 11, 10, 6, 5], [11, 0, 8, 11, 2, 0, 10, 6, 5],
    [0, 1, 9, 2, 3, 11, 5, 10, 6], [5, 10, 6, 1, 9, 2, 9, 11, 2, 9, 8, 11],
    [6, 3, 11, 6, 5, 3, 5, 1, 3], [0, 8, 11, 0, 11, 5, 0, 5, 1, 5, 11, 6],
    [3, 11, 6, 0, 3, 6, 0, 6, 5, 0, 5, 9], [6, 5, 9, 6, 9, 11, 11, 9, 8],
    [5, 10, 6, 4, 7, 8], [4, 3, 0, 4, 7, 3, 6, 5, 10], [1, 9, 0, 5, 10, 6, 8, 4, 7],
    [10, 6, 5, 1, 9, 7, 1, 7, 3, 7, 9, 4], [6, 1, 2, 6, 5, 1, 4, 7, 8],
    [1, 2, 5, 5, 2, 6, 3, 0, 4, 3, 4, 7], [8, 4, 7, 9, 0, 5, 0, 6, 5, 0, 2, 6],
    [7, 3, 9, 7, 9, 4, 3, 2, 9, 5, 9, 6, 2, 6, 9], [3, 11, 2, 7, 8, 4, 10, 6, 5],
    [5, 10, 6, 4, 7, 2, 4, 2, 0, 2, 7, 11], [0, 1, 9, 4, 7, 8, 2, 3, 11, 5, 10, 6],
    [9, 2, 1, 9, 11, 2, 9, 4, 11, 7, 11, 4, 5, 10, 6], [8, 4, 7, 3, 11, 5, 3, 5, 1, 5, 11, 6],
    [5, 1, 11, 5, 11, 6, 1, 0, 11, 7, 11, 4, 0, 4, 11], [0, 5, 9, 0, 6, 5, 0, 3, 6, 11, 6, 3, 8, 4, 7],
    [6, 5, 9, 6, 9, 11, 4, 7, 9, 7, 11, 9], [10, 4, 9, 6, 4, 10], [4, 10, 6, 4, 9, 10, 0, 8, 3],
    [10, 0, 1, 10, 6, 0, 6, 4, 0], [8, 3, 1, 8, 1, 6, 8, 6, 4, 6, 1, 10],
    [1, 4, 9, 1, 2, 4, 2, 6, 4], [3, 0, 8, 1, 2, 9, 2, 4, 9, 2, 6, 4],
    [0, 2, 4, 4, 2, 6], [8, 3, 2, 8, 2, 4, 4, 2, 6], [10, 4, 9, 10, 6, 4, 11, 2, 3],
    [0, 8, 2, 2, 8, 11, 4, 9, 10, 4, 10, 6], [3, 11, 2, 0, 1, 6, 0, 6, 4, 6, 1, 10],
    [6, 4, 1, 6, 1, 10, 4, 8, 1, 2, 1, 11, 8, 11, 1], [9, 6, 4, 9, 3, 6, 9, 1, 3, 11, 6, 3],
    [8, 11, 1, 8, 1, 0, 11, 6, 1, 9, 1, 4, 6, 4, 1], [3, 11, 6, 3, 6, 0, 0, 6, 4],
    [6, 4, 8, 11, 6, 8], [7, 10, 6, 7, 8, 10, 8, 9, 10], [0, 7, 3, 0, 10, 7, 0, 9, 10, 6, 7, 10],
    [10, 6, 7, 1, 10, 7, 1, 7, 8, 1, 8, 0], [10, 6, 7, 10, 7, 1, 1, 7, 3],
    [1, 2, 6, 1, 6, 8, 1, 8, 9, 8, 6, 7], [2, 6, 9, 2, 9, 1, 6, 7, 9, 0, 9, 3, 7, 3, 9],
    [7, 8, 0, 7, 0, 6, 6, 0, 2], [7, 3, 2, 6, 7, 2], [2, 3, 11, 10, 6, 8, 10, 8, 9, 8, 6, 7],
    [2, 0, 7, 2, 7, 11, 0, 9, 7, 6, 7, 10, 9, 10, 7], [1, 8, 0, 1, 7, 8, 1, 10, 7, 6, 7, 10, 2, 3, 11],
    [11, 2, 1, 11, 1, 7, 10, 6, 1, 6, 7, 1], [8, 9, 6, 8, 6, 7, 9, 1, 6, 11, 6, 3, 1, 3, 6],
    [0, 9, 1, 11, 6, 7], [7, 8, 0, 7, 0, 6, 3, 11, 0, 11, 6, 0], [7, 11, 6],
    [7, 6, 11], [3, 0, 8, 11, 7, 6], [0, 1, 9, 11, 7, 6], [8, 1, 9, 8, 3, 1, 11, 7, 6],
    [10, 1, 2, 6, 11, 7], [1, 2, 10, 3, 0, 8, 6, 11, 7], [2, 9, 0, 2, 10, 9, 6, 11, 7],
    [6, 11, 7, 2, 10, 3, 10, 8, 3, 10, 9, 8], [7, 2, 3, 6, 2, 7], [7, 0, 8, 7, 6, 0, 6, 2, 0],
    [2, 7, 6, 2, 3, 7, 0, 1, 9], [1, 6, 2, 1, 8, 6, 1, 9, 8, 8, 7, 6],
    [10, 7, 6, 10, 1, 7, 1, 3, 7], [10, 7, 6, 1, 7, 10, 1, 8, 7, 1, 0, 8],
    [0, 3, 7, 0, 7, 10, 0, 10, 9, 6, 10, 7], [7, 6, 10, 7, 10, 8, 8, 10, 9],
    [6, 8, 4, 11, 8, 6], [3, 6, 11, 3, 0, 6, 0, 4, 6], [8, 6, 11, 8, 4, 6, 9, 0, 1],
    [9, 4, 6, 9, 6, 3, 9, 3, 1, 11, 3, 6], [6, 8, 4, 6, 11, 8, 2, 10, 1],
    [1, 2, 10, 3, 0, 11, 0, 6, 11, 0, 4, 6], [4, 11, 8, 4, 6, 11, 0, 2, 9, 2, 10, 9],
    [10, 9, 3, 10, 3, 2, 9, 4, 3, 11, 3, 6, 4, 6, 3], [8, 2, 3, 8, 4, 2, 4, 6, 2],
    [0, 4, 2, 4, 6, 2], [1, 9, 0, 2, 3, 4, 2, 4, 6, 4, 3, 8], [1, 9, 4, 1, 4, 2, 2, 4, 6],
    [8, 1, 3, 8, 6, 1, 8, 4, 6, 6, 10, 1], [10, 1, 0, 10, 0, 6, 6, 0, 4],
    [4, 6, 3, 4, 3, 8, 6, 10, 3, 0, 3, 9, 10, 9, 3], [10, 9, 4, 6, 10, 4],
    [4, 9, 5, 7, 6, 11], [0, 8, 3, 4, 9, 5, 11, 7, 6], [5, 0, 1, 5, 4, 0, 7, 6, 11],
    [11, 7, 6, 8, 3, 4, 3, 5, 4, 3, 1, 5], [9, 5, 4, 10, 1, 2, 7, 6, 11],
    [6, 11, 7, 1, 2, 10, 0, 8, 3, 4, 9, 5], [7, 6, 11, 5, 4, 10, 4, 2, 10, 4, 0, 2],
    [3, 4, 8, 3, 5, 4, 3, 2, 5, 10, 5, 2, 11, 7, 6], [7, 2, 3, 7, 6, 2, 5, 4, 9],
    [9, 5, 4, 0, 8, 6, 0, 6, 2, 6, 8, 7], [3, 6, 2, 3, 7, 6, 1, 5, 0, 5, 4, 0],
    [6, 2, 8, 6, 8, 7, 2, 1, 8, 4, 8, 5, 1, 5, 8], [9, 5, 4, 10, 1, 6, 1, 7, 6, 1, 3, 7],
    [1, 6, 10, 1, 7, 6, 1, 0, 7, 8, 7, 0, 9, 5, 4], [4, 0, 10, 4, 10, 5, 0, 3, 10, 6, 10, 7, 3, 7, 10],
    [7, 6, 10, 7, 10, 8, 5, 4, 10, 4, 8, 10], [6, 9, 5, 6, 11, 9, 11, 8, 9],
    [3, 6, 11, 0, 6, 3, 0, 5, 6, 0, 9, 5], [0, 11, 8, 0, 5, 11, 0, 1, 5, 5, 6, 11],
    [6, 11, 3, 6, 3, 5, 5, 3, 1], [1, 2, 10, 9, 5, 11, 9, 11, 8, 11, 5, 6],
    [0, 11, 3, 0, 6, 11, 0, 9, 6, 5, 6, 9, 1, 2, 10], [11, 8, 5, 11, 5, 6, 8, 0, 5, 10, 5, 2, 0, 2, 5],
    [6, 11, 3, 6, 3, 5, 2, 10, 3, 10, 5, 3], [5, 8, 9, 5, 2, 8, 5, 6, 2, 3, 8, 2],
    [9, 5, 6, 9, 6, 0, 0, 6, 2], [1, 5, 8, 1, 8, 0, 5, 6, 8, 3, 8, 2, 6, 2, 8],
    [1, 5, 6, 2, 1, 6], [1, 3, 6, 1, 6, 10, 3, 8, 6, 5, 6, 9, 8, 9, 6],
    [10, 1, 0, 10, 0, 6, 9, 5, 0, 5, 6, 0], [0, 3, 8, 5, 6, 10], [10, 5, 6],
    [11, 5, 10, 7, 5, 11], [11, 5, 10, 11, 7, 5, 8, 3, 0], [5, 11, 7, 5, 10, 11, 1, 9, 0],
    [10, 7, 5, 10, 11, 7, 9, 8, 1, 8, 3, 1], [11, 1, 2, 11, 7, 1, 7, 5, 1],
    [0, 8, 3, 1, 2, 7, 1, 7, 5, 7, 2, 11], [9, 7, 5, 9, 2, 7, 9, 0, 2, 2, 11, 7],
    [7, 5, 2, 7, 2, 11, 5, 9, 2, 3, 2, 8, 9, 8, 2], [2, 5, 10, 2, 3, 5, 3, 7, 5],
    [8, 2, 0, 8, 5, 2, 8, 7, 5, 10, 2, 5], [9, 0, 1, 5, 10, 3, 5, 3, 7, 3, 10, 2],
    [9, 8, 2, 9, 2, 1, 8, 7, 2, 10, 2, 5, 7, 5, 2], [1, 3, 5, 3, 7, 5],
    [0, 8, 7, 0, 7, 1, 1, 7, 5], [9, 0, 3, 9, 3, 5, 5, 3, 7], [9, 8, 7, 5, 9, 7],
    [5, 8, 4, 5, 10, 8, 10, 11, 8], [5, 0, 4, 5, 11, 0, 5, 10, 11, 11, 3, 0],
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
    [4, 8, 7], [9, 10, 8, 10, 11, 8], [3, 0, 9, 3, 9, 11, 11, 9, 10], [0, 1, 10, 0, 10, 8, 8, 10, 11],
    [3, 1, 10, 11, 3, 10], [1, 2, 11, 1, 11, 9, 9, 11, 8], [3, 0, 9, 3, 9, 11, 1, 2, 9, 2, 11, 9],
    [0, 2, 11, 8, 0, 11], [3, 2, 11], [2, 3, 8, 2, 8, 10, 10, 8, 9], [9, 10, 2, 0, 9, 2],
    [2, 3, 8, 2, 8, 10, 0, 1, 8, 1, 10, 8], [1, 10, 2], [1, 3, 8, 9, 1, 8], [0, 9, 1], [0, 3, 8], []
]

# Metaball class
class Metaball:
    def __init__(self, x, y, z, radius, strength=1.0):
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.strength = strength

    def field_value(self, px, py, pz):
        """Calculate field value at point (px, py, pz)"""
        dx = px - self.x
        dy = py - self.y
        dz = pz - self.z
        dist_sq = dx*dx + dy*dy + dz*dz
        if dist_sq < 0.0001:  # Avoid division by zero
            return self.strength * 1000
        return self.strength * (self.radius * self.radius) / dist_sq

# Metaballs generator class
class MetaballsGenerator:
    def __init__(self, metaballs, threshold=1.0, resolution=20):
        self.metaballs = metaballs
        self.threshold = threshold
        self.resolution = resolution

    def evaluate_field(self, x, y, z):
        """Evaluate the combined field value at point (x, y, z)"""
        value = 0.0
        for ball in self.metaballs:
            value += ball.field_value(x, y, z)
        return value

    def get_bounds(self):
        """Calculate bounding box for all metaballs"""
        if not self.metaballs:
            return (-5, 5, -5, 5, -5, 5)

        padding = 2.0
        min_x = min(ball.x - ball.radius - padding for ball in self.metaballs)
        max_x = max(ball.x + ball.radius + padding for ball in self.metaballs)
        min_y = min(ball.y - ball.radius - padding for ball in self.metaballs)
        max_y = max(ball.y + ball.radius + padding for ball in self.metaballs)
        min_z = min(ball.z - ball.radius - padding for ball in self.metaballs)
        max_z = max(ball.z + ball.radius + padding for ball in self.metaballs)

        return (min_x, max_x, min_y, max_y, min_z, max_z)

    def interpolate_vertex(self, p1, p2, v1, v2):
        """Interpolate vertex position between two points"""
        if abs(self.threshold - v1) < 0.00001:
            return p1
        if abs(self.threshold - v2) < 0.00001:
            return p2
        if abs(v1 - v2) < 0.00001:
            return p1

        mu = (self.threshold - v1) / (v2 - v1)
        return [
            p1[0] + mu * (p2[0] - p1[0]),
            p1[1] + mu * (p2[1] - p1[1]),
            p1[2] + mu * (p2[2] - p1[2])
        ]

    def generate_mesh(self):
        """Generate mesh using Marching Cubes algorithm"""
        vertices = []
        triangles = []

        bounds = self.get_bounds()
        min_x, max_x, min_y, max_y, min_z, max_z = bounds

        step = (max_x - min_x) / self.resolution

        # Marching cubes implementation
        for i in range(self.resolution):
            for j in range(self.resolution):
                for k in range(self.resolution):
                    x = min_x + i * step
                    y = min_y + j * step
                    z = min_z + k * step

                    # Cube vertices
                    cube_verts = [
                        [x, y, z],
                        [x + step, y, z],
                        [x + step, y, z + step],
                        [x, y, z + step],
                        [x, y + step, z],
                        [x + step, y + step, z],
                        [x + step, y + step, z + step],
                        [x, y + step, z + step]
                    ]

                    # Evaluate field at each vertex
                    cube_vals = [self.evaluate_field(v[0], v[1], v[2]) for v in cube_verts]

                    # Determine cube index
                    cube_index = 0
                    for vi in range(8):
                        if cube_vals[vi] < self.threshold:
                            cube_index |= (1 << vi)

                    # Skip if cube is entirely inside or outside
                    if cube_index == 0 or cube_index == 255:
                        continue

                    # Get edge intersections
                    edge_verts = [None] * 12

                    if edgeTable[cube_index] & 1:
                        edge_verts[0] = self.interpolate_vertex(cube_verts[0], cube_verts[1], cube_vals[0], cube_vals[1])
                    if edgeTable[cube_index] & 2:
                        edge_verts[1] = self.interpolate_vertex(cube_verts[1], cube_verts[2], cube_vals[1], cube_vals[2])
                    if edgeTable[cube_index] & 4:
                        edge_verts[2] = self.interpolate_vertex(cube_verts[2], cube_verts[3], cube_vals[2], cube_vals[3])
                    if edgeTable[cube_index] & 8:
                        edge_verts[3] = self.interpolate_vertex(cube_verts[3], cube_verts[0], cube_vals[3], cube_vals[0])
                    if edgeTable[cube_index] & 16:
                        edge_verts[4] = self.interpolate_vertex(cube_verts[4], cube_verts[5], cube_vals[4], cube_vals[5])
                    if edgeTable[cube_index] & 32:
                        edge_verts[5] = self.interpolate_vertex(cube_verts[5], cube_verts[6], cube_vals[5], cube_vals[6])
                    if edgeTable[cube_index] & 64:
                        edge_verts[6] = self.interpolate_vertex(cube_verts[6], cube_verts[7], cube_vals[6], cube_vals[7])
                    if edgeTable[cube_index] & 128:
                        edge_verts[7] = self.interpolate_vertex(cube_verts[7], cube_verts[4], cube_vals[7], cube_vals[4])
                    if edgeTable[cube_index] & 256:
                        edge_verts[8] = self.interpolate_vertex(cube_verts[0], cube_verts[4], cube_vals[0], cube_vals[4])
                    if edgeTable[cube_index] & 512:
                        edge_verts[9] = self.interpolate_vertex(cube_verts[1], cube_verts[5], cube_vals[1], cube_vals[5])
                    if edgeTable[cube_index] & 1024:
                        edge_verts[10] = self.interpolate_vertex(cube_verts[2], cube_verts[6], cube_vals[2], cube_vals[6])
                    if edgeTable[cube_index] & 2048:
                        edge_verts[11] = self.interpolate_vertex(cube_verts[3], cube_verts[7], cube_vals[3], cube_vals[7])

                    # Create triangles
                    tri_list = triTable[cube_index]
                    for ti in range(0, len(tri_list), 3):
                        if ti + 2 < len(tri_list):
                            v1 = edge_verts[tri_list[ti]]
                            v2 = edge_verts[tri_list[ti + 1]]
                            v3 = edge_verts[tri_list[ti + 2]]

                            if v1 and v2 and v3:
                                idx = len(vertices)
                                vertices.extend([v1, v2, v3])
                                triangles.append([idx, idx + 1, idx + 2])

        return vertices, triangles

# Command event handlers
class MetaballsCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            cmd = args.command
            inputs = cmd.commandInputs

            # Number of metaballs
            inputs.addIntegerSpinnerCommandInput('numBalls', 'Number of Metaballs', 1, 10, 1, 3)

            # Resolution
            inputs.addIntegerSpinnerCommandInput('resolution', 'Resolution', 10, 50, 1, 20)

            # Threshold
            inputs.addFloatSpinnerCommandInput('threshold', 'Threshold', '', 0.1, 5.0, 0.1, 1.0)

            # Random seed
            inputs.addIntegerSpinnerCommandInput('seed', 'Random Seed', 1, 1000, 1, 42)

            # Bounding box size
            inputs.addFloatSpinnerCommandInput('boundingSize', 'Bounding Size (cm)', 'cm', 1.0, 50.0, 0.5, 10.0)

            # Connect to execute event
            onExecute = MetaballsCommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

        except:
            _ui.messageBox('Failed to create command:\n{}'.format(traceback.format_exc()))

class MetaballsCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            # Get input values
            inputs = args.command.commandInputs
            numBalls = inputs.itemById('numBalls').value
            resolution = inputs.itemById('resolution').value
            threshold = inputs.itemById('threshold').value
            seed = inputs.itemById('seed').value
            boundingSize = inputs.itemById('boundingSize').value

            # Generate random metaballs
            import random
            random.seed(seed)

            metaballs = []
            for i in range(numBalls):
                x = random.uniform(-boundingSize/2, boundingSize/2)
                y = random.uniform(-boundingSize/2, boundingSize/2)
                z = random.uniform(-boundingSize/2, boundingSize/2)
                radius = random.uniform(boundingSize/10, boundingSize/4)
                strength = random.uniform(0.8, 1.2)
                metaballs.append(Metaball(x, y, z, radius, strength))

            # Generate mesh
            generator = MetaballsGenerator(metaballs, threshold, resolution)
            vertices, triangles = generator.generate_mesh()

            if not vertices or not triangles:
                _ui.messageBox('No mesh generated. Try adjusting parameters.')
                return

            # Create mesh in Fusion 360
            create_mesh_body(vertices, triangles)

            _ui.messageBox('Metaballs created successfully!\nVertices: {}\nTriangles: {}'.format(
                len(vertices), len(triangles)))

        except:
            _ui.messageBox('Failed to execute command:\n{}'.format(traceback.format_exc()))

def create_mesh_body(vertices, triangles):
    """Create a mesh body in Fusion 360"""
    try:
        # Get the active design
        product = _app.activeProduct
        design = adsk.fusion.Design.cast(product)
        rootComp = design.rootComponent

        # Create a new component
        occurrence = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        newComp = occurrence.component
        newComp.name = 'Metaballs'

        # Create base feature
        baseFeature = newComp.features.baseFeatures.add()
        baseFeature.startEdit()

        # Create mesh
        meshBuilder = adsk.fusion.MeshBodyBuilder.create()

        # Add vertices
        for v in vertices:
            meshBuilder.addVertex(adsk.core.Point3D.create(v[0], v[1], v[2]))

        # Add triangles
        for tri in triangles:
            meshBuilder.addTriangle(tri[0], tri[1], tri[2])

        # Create mesh body
        meshBody = meshBuilder.createMeshBody()

        # Add to component
        bodies = newComp.bRepBodies
        bodies.add(meshBody, baseFeature)

        baseFeature.finishEdit()

        # Convert to BRep if possible (for better editing)
        try:
            # Get the mesh body
            meshBodies = newComp.meshBodies
            if meshBodies.count > 0:
                meshBodyItem = meshBodies.item(0)
                # Convert to BRep
                convertFeature = newComp.features.brepFeatures.add(meshBodyItem)
        except:
            pass  # Continue even if conversion fails

    except:
        _ui.messageBox('Failed to create mesh body:\n{}'.format(traceback.format_exc()))

def run(context):
    """Called when the add-in is run"""
    try:
        global _app, _ui, _cmdDef
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        # Get the CommandDefinitions collection
        cmdDefs = _ui.commandDefinitions

        # Create command definition
        _cmdDef = cmdDefs.itemById(CMD_ID)
        if _cmdDef:
            _cmdDef.deleteMe()

        # Get icon path
        iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')

        _cmdDef = cmdDefs.addButtonDefinition(
            CMD_ID,
            CMD_NAME,
            CMD_DESCRIPTION,
            iconPath
        )

        # Connect to command created event
        onCommandCreated = MetaballsCommandCreatedHandler()
        _cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Get the target workspace and panel
        workspace = _ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)

        # Add the button to the panel
        buttonControl = panel.controls.addCommand(_cmdDef)
        buttonControl.isPromotedByDefault = True
        buttonControl.isPromoted = True

        _ui.messageBox('Metaballs add-in loaded successfully!')

    except:
        if _ui:
            _ui.messageBox('Failed to run add-in:\n{}'.format(traceback.format_exc()))

def stop(context):
    """Called when the add-in is stopped"""
    try:
        global _ui, _cmdDef

        # Get the target workspace and panel
        workspace = _ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)

        # Delete the button
        buttonControl = panel.controls.itemById(CMD_ID)
        if buttonControl:
            buttonControl.deleteMe()

        # Delete the command definition
        cmdDef = _ui.commandDefinitions.itemById(CMD_ID)
        if cmdDef:
            cmdDef.deleteMe()

    except:
        if _ui:
            _ui.messageBox('Failed to stop add-in:\n{}'.format(traceback.format_exc()))
