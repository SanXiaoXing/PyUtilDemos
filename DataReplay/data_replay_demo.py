import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvas
import pandas as pd