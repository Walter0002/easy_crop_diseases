# encoding: utf-8
"""
import path
"""

import os.path as osp
import sys


def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)


this_dir = osp.dirname(__file__)
add_path(this_dir)

# Add lib to PYTHONPATH
src_path = osp.join(this_dir, 'src')
add_path(src_path)

resources_path = osp.join(this_dir, 'resources')
add_path(resources_path)
