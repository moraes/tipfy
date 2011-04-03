# -*- coding: utf-8 -*-
"""Sets sys.path for the library directories."""
import os
import sys

current_path = os.path.abspath(os.path.dirname(__file__))

# Add lib as primary libraries directory, with fallback to lib/dist
# and optionally to lib/dist.zip, loaded using zipimport.
sys.path[0:0] = [
    os.path.join(current_path, 'lib'),
    os.path.join(current_path, 'lib', 'dist'),
    os.path.join(current_path, 'lib', 'dist.zip'),
]
