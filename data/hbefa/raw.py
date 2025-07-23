from synpp import ConfigurationContext, ExecuteContext, ValidateContext
import os
import shutil

GH_URL = "https://github.com/matsim-org/matsim-libs/raw/refs/heads/main/examples/scenarios/emissions-sampleScenario/"

COLD_AVG = "sample_41_EFA_ColdStart_vehcat_2020average.csv"
HOT_AVG = "sample_41_EFA_HOT_vehcat_2020average.csv"
COLD_DETAILED = "sample_41_EFA_ColdStart_SubSegm_2020detailed.csv"
HOT_DETAILED = "sample_41_EFA_HOT_SubSegm_2020detailed.csv"

def configure(context: ConfigurationContext):
    context.config("data_path")
    context.config("hbefa_path", "hbefa")

    context.config("hbefa_cold_average", "")
    context.config("hbefa_cold_detailed", "")
    context.config("hbefa_hot_average", "")
    context.config("hbefa_hot_detailed", "")

def execute(context: ExecuteContext):

    hbefa_path = "%s/%s" % (context.config("data_path"), context.config("hbefa_path"))

    hbefa_cold_average = context.config("hbefa_cold_average")
    hbefa_hot_average = context.config("hbefa_hot_average")

    hbefa_cold_detailed = context.config("hbefa_cold_detailed")
    hbefa_hot_detailed = context.config("hbefa_hot_detailed")

    if hbefa_cold_average == "" or hbefa_hot_average == "":
        
        hbefa_cold_average_path = "%s/%s" % (context.path(), COLD_AVG)
        hbefa_hot_average_path = "%s/%s" % (context.path(), HOT_AVG)
        hbefa_cold_detailed_path = "%s/%s" % (context.path(), COLD_DETAILED)
        hbefa_hot_detailed_path = "%s/%s" % (context.path(), HOT_DETAILED)

        import urllib.request

        os.makedirs(hbefa_path, exist_ok=True)

        cold_avg_url = GH_URL + COLD_AVG
        hot_avg_url = GH_URL + HOT_AVG
        cold_detailed_url = GH_URL + COLD_DETAILED
        hot_detailed_url = GH_URL + HOT_DETAILED

        urllib.request.urlretrieve(cold_avg_url, hbefa_cold_average_path)
        urllib.request.urlretrieve(hot_avg_url, hbefa_hot_average_path)

        urllib.request.urlretrieve(cold_detailed_url, hbefa_cold_detailed_path)
        urllib.request.urlretrieve(hot_detailed_url, hbefa_hot_detailed_path)

        return COLD_AVG, HOT_AVG, COLD_DETAILED, HOT_DETAILED
    
    # else just copy all 4 files int context.path()

    for file in [hbefa_cold_average, hbefa_hot_average, hbefa_cold_detailed, hbefa_hot_detailed]:
        init_path = "%s/%s" % (hbefa_path, file)
        result_path = "%s/%s" % (context.path(), file)

        shutil.copy(init_path, result_path)

    return hbefa_cold_average, hbefa_hot_average, hbefa_cold_detailed, hbefa_hot_detailed

def validate(context: ValidateContext):
    hbefa_path = "%s/%s" % (context.config("data_path"), context.config("hbefa_path"))

    hbefa_cold_average = context.config("hbefa_cold_average")
    hbefa_hot_average = context.config("hbefa_hot_average")

    hbefa_cold_detailed = context.config("hbefa_cold_detailed")
    hbefa_hot_detailed = context.config("hbefa_hot_detailed")


    if hbefa_cold_average == "" or hbefa_hot_average == "":
        print("WARINING: HBEFA cold and hot average files are required. will use default ones from matsim.exemples (%s)" % GH_URL)
        return
    
    hbefa_cold_average_path = "%s/%s" % (hbefa_path, hbefa_cold_average)
    hbefa_hot_average_path = "%s/%s" % (hbefa_path, hbefa_hot_average)
    hbefa_cold_detailed_path = "%s/%s" % (hbefa_path, hbefa_cold_detailed)
    hbefa_hot_detailed_path = "%s/%s" % (hbefa_path, hbefa_hot_detailed)

    if not os.path.exists(hbefa_cold_average_path):
        raise FileNotFoundError(f"HBEFA cold average file not found: {hbefa_cold_average_path}")
    if not os.path.exists(hbefa_hot_average_path):
        raise FileNotFoundError(f"HBEFA hot average file not found: {hbefa_hot_average_path}")
    if not os.path.exists(hbefa_cold_detailed_path):
        raise FileNotFoundError(f"HBEFA cold detailed file not found: {hbefa_cold_detailed_path}")
    if not os.path.exists(hbefa_hot_detailed_path):
        raise FileNotFoundError(f"HBEFA hot detailed file not found: {hbefa_hot_detailed_path}")
    