"""
The goal of this stage is to output attractors for the force model. Get weight from bpe processing to represent each location capacity.
"""

def configure(context):
    context.stage("synthesis.locations.secondary")

def execute(context):
    # load all secondary activity locations
    df_attractors = context.stage("synthesis.locations.secondary")[["activity_type","weight", "geometry"]].copy()
    df_attractors = df_attractors[df_attractors["activity_type"]!="education"]

    return df_attractors
