from synpp import ConfigurationContext, ExecuteContext
from pathlib import Path
import noise.runtime.noisemodelling as noisemodelling

def configure(context: ConfigurationContext):
    context.stage("noise.runtime.noisemodelling")
    context.stage("noise.simulation.prepare")

def execute(context: ExecuteContext):
    
    properties_path = context.stage("noise.simulation.prepare")
    
    noisemodelling.run(context, [
        "-conf", Path(properties_path).as_posix(),
        "-osm",
        "--reflOrder", "1",
        "--maxReflDist", "10",
        "--maxSrcDist", "50",
        "--timeBinMin", "0",
        "--timeBinMax", "86400",
        "--timeBinSize", "900",
    ])
