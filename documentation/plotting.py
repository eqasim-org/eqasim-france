import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as tck
import palettable

SHORT_FIGSIZE = (3.0, 2.5)
WIDE_FIGSIZE = (6.0, 2.5)

DPI = 300
FONT_SIZE = 8

COLORSET =  palettable.colorbrewer.qualitative.Set2_4.mpl_colors
COLORSET5 =  palettable.colorbrewer.qualitative.Set2_5.mpl_colors
COLORS = {
    "census": COLORSET[2],
    "entd": COLORSET[0],
    "egt": COLORSET[1],
    "synthetic": "#cccccc", #COLORSET[3]
}

MODE_LABELS = dict(
    car = "Car driver",
    car_passenger = "Car passenger",
    pt = "Public transport",
    bicycle = "Bicycle",
    walk = "Walking"
)

def setup():
    plt.rc("font", family = "serif", size = FONT_SIZE)
    plt.rc("figure", dpi = DPI, figsize = SHORT_FIGSIZE)
    plt.rc("legend", fontsize = FONT_SIZE, loc = "best", fancybox = False)
    plt.rc("grid", linewidth = 0.5)
    plt.rc("patch", linewidth = 0.5)
    plt.rc("mathtext", fontset = "cm")
