from synpp import ConfigurationContext, ExecuteContext
from pathlib import Path
import noise.runtime.noisemodelling as noisemodelling

def configure(context: ConfigurationContext):
    context.stage("noise.runtime.noisemodelling")
    context.stage("noise.simulation.prepare")

    context.config("noise.compute", "exposure")

    context.config("noise.time_bin_size", 3600)
    context.config("noise.time_bin_min", 0)
    context.config("noise.time_bin_max", 86400)

    context.config("noise.refl_order", 1)
    context.config("noise.max_refl_dist", 50)
    context.config("noise.max_src_dist", 750)

def execute(context: ExecuteContext):
    
    properties_path = context.stage("noise.simulation.prepare")
    
    args = [
        "--configFile", Path(properties_path).as_posix(),
        "--importOsmPbf",
        "--runSimulation",
        "--reflOrder", str(context.config("noise.refl_order")),
        "--maxReflDist", str(context.config("noise.max_refl_dist")),
        "--maxSrcDist", str(context.config("noise.max_src_dist")),
        "--timeBinMin", str(context.config("noise.time_bin_min")),
        "--timeBinMax", str(context.config("noise.time_bin_max")),
        "--timeBinSize", str(context.config("noise.time_bin_size")),
        "--exportBuildings",
        "--exportResults"
    ]

    if context.config("noise.compute") == "maps":
        args += ["--compute", "maps"]

    noisemodelling.run(context, args)
