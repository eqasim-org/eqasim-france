"""
The goal of this stage is to output attractors for the force model. In the simplest case, we
assign a weight of 1.0 to every activity location.
"""

def configure(context):
    context.stage("synthesis.locations.secondary")

def execute(context):
    # load all secondary activity locations
    df_attractors = context.stage("synthesis.locations.secondary")[["activity_type", "geometry"]].copy()
    df_attractors = df_attractors[df_attractors["activity_type"].isin(["shop", "leisure", "other"])]

    # assign a weight of one to every secondary activity location
    df_attractors["weight"] = 1.0

    return df_attractors
