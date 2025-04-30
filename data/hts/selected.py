import pandas as pd
import numpy as np

def configure(context):
    hts = context.config("hts")

    if hts == "egt":
        context.stage("data.hts.egt.filtered", alias = "hts")
    elif hts == "entd":
        context.stage("data.hts.entd.reweighted", alias = "hts")
    elif hts == "edgt_lyon":
        context.stage("data.hts.edgt_lyon.reweighted", alias = "hts")
    elif hts == "edgt_44":
        context.stage("data.hts.edgt_44.reweighted", alias = "hts")
    elif hts == "emp":
        context.stage("data.hts.emp.reweighted", alias = "hts")
    else:
        raise RuntimeError("Unknown HTS: %s" % hts)

def execute(context):
    return context.stage("hts")
