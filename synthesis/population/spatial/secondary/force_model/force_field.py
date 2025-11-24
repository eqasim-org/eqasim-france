import numpy as np

def configure(context):
    context.config("processes")

    attractors = context.config("secondary_activities.force_model.attractors", "uniform")
    context.config("secondary_activities.force_model.cell_size", 250.0)
    context.config("secondary_activities.force_model.grid_margin", 2000.0)

    context.stage("synthesis.population.spatial.secondary.force_model.attractors.{}".format(attractors), 
        alias = "attractors")

def process(context, attractors):
    """
    calculates a partial field across all coodinates for a (partial) set of attractors
    """
    coordinates = context.data("coordinates")

    field = np.zeros(coordinates.shape)
    for attractor in attractors:
        delta = attractor[:2] - coordinates
        norm = np.linalg.norm(delta, axis = - 1)
        norm[norm < 1.0] = 125.0 # prevent division by zero
        field += attractor[2] * delta / (norm**3)[..., np.newaxis]
        context.progress.update()
    
    return field

def execute(context):
    # load attractors
    df_attractors = context.stage("attractors")

    # configuration
    cell_size = context.config("secondary_activities.force_model.cell_size")
    grid_margin = context.config("secondary_activities.force_model.grid_margin")
    processes = context.config("processes")

    # attractor bounds
    xmin, xmax = min(df_attractors.geometry.x), max(df_attractors.geometry.x)
    ymin, ymax = min(df_attractors.geometry.y), max(df_attractors.geometry.y)

    # spacing
    nx = int(np.ceil((xmax - xmin + 2 * grid_margin) / cell_size)) + 1
    ny = int(np.ceil((ymax - ymin + 2 * grid_margin) / cell_size)) + 1

    # construct grid
    xv = xmin - grid_margin + np.arange(nx) * cell_size
    yv = ymin - grid_margin + np.arange(ny) * cell_size
    xm, ym = np.meshgrid(xv, yv, indexing = "ij")

    # construct the force fields by activity type
    fields = {}

    for activity_type in df_attractors["activity_type"].unique():
        df_selection = df_attractors[df_attractors["activity_type"] == activity_type]

        coordinates = np.stack([xm, ym], axis = -1)
        field = np.zeros(coordinates.shape)

        # parallel execution
        tasks = np.array([[attractor["geometry"].x, attractor["geometry"].y, attractor["weight"]] for _, attractor in df_selection.iterrows()])
        batches = np.array_split(tasks, processes)

        with context.progress(label = "Computing force field for {}".format(activity_type), total = len(df_selection)):
            with context.parallel(processes = processes, data = { "coordinates": coordinates }) as parallel:
                for partial in parallel.map(process, batches):
                    field += partial

        fields[activity_type] = field

    # output grid parameters
    grid_parameters = {
        "xmin": xmin - grid_margin,
        "ymin": ymin - grid_margin,
        "cell_size": cell_size,
        "nx": nx,
        "ny": ny
    }

    return grid_parameters, fields
