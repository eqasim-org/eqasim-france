from synpp import ConfigurationContext, ExecuteContext
from pathlib import Path
import noise.runtime.noisemodelling as noisemodelling

def configure(context: ConfigurationContext):
    context.stage("noise.runtime.noisemodelling")
    context.stage("noise.simulation.prepare")

    context.config("noise_computation", "exposure")

def execute(context: ExecuteContext):
    
    properties_path = context.stage("noise.simulation.prepare")
    
    args = [
        "--configFile", Path(properties_path).as_posix(),
        "--importOsmPbf",
        "--runSimulation",
        "--reflOrder", "1",
        "--maxReflDist", "10",
        "--maxSrcDist", "50",
        "--timeBinMin", "0",
        "--timeBinMax", "86400",
        "--timeBinSize", "900",
        "--exportBuildings",
        "--exportResults"
    ]

    if context.config("noise_computation") == "maps":
        args.append("--compute", "maps")

    noisemodelling.run(context, args)
