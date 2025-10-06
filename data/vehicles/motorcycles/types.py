import pandas as pd

"""
This stage creates the various type of motorcycles needed for the simulation with HBEFA emissions
"""

MOTORCYLE_SIZES = ["<=50cc", "<=125cc", "<=250cc", ">250cc"]

def configure(context):
    pass

def execute(context):

    default_motorcycle_type = {
        'type_id': 'default_motorcycle', 'nb_seats': 1, 'length': 2.0, 'width': 1.0, 'pce': 1.0, 'mode': "motorcycle",
        'hbefa_cat': "motorcycle", 'hbefa_tech': "average", 'hbefa_size': "average", 'hbefa_emission': "average",
        'cnossos_cat': "4a"  # 4a for motorcycles <=125cc in CNOSSOS-EU
    }
    motorcycle_types = [default_motorcycle_type]

    for size in MOTORCYLE_SIZES:
        if size == "<=50cc":
            cnossos_cat = "4a"  # 4b for motorcycles <=125cc in CNOSSOS-EU
            hbefa_size = "<=50cc"
            hbefa_tech = "petrol (2S)"
            for vmax, hbefa_prefix in [("30kmh", "Moped-EU"), ("50kmh", "SMC Euro-")]:
                for euro in ["0", "1", "2", "3", "4", "5"]:
                    id = f"motorcycle_lte_50cc_{vmax}_euro_{euro}_cnossos_{cnossos_cat}"
                    hbefa_emission = f"{hbefa_prefix}{euro}"
                    motorcycle_types.append({
                        'type_id': id, 'nb_seats': 1, 'length': 2.0, 'width': 1.0, 'pce': 1.0, 'mode': "motorcycle",
                        'hbefa_cat': "motorcycle", 'hbefa_tech': hbefa_tech, 'hbefa_size': hbefa_size, 'hbefa_emission': hbefa_emission,
                        'cnossos_cat': cnossos_cat
                    })
        elif size == "<=125cc":
            cnossos_cat = "4a"  # 4a for motorcycles <=125cc in CNOSSOS-EU
            hbefa_size = "<=250cc"
            for hbefa_tech, hbefa_prefix in [("petrol (2S)", "MC-2S Euro-"), ("petrol (4S)", "MC 4S Euro-")]:
                for euro in ["0", "1", "2", "3", "4", "5", "6"]:
                    id = f"motorcycle_lte_250cc_{hbefa_tech[8:10]}_euro_{euro}_cnossos_{cnossos_cat}"
                    hbefa_emission = f"{hbefa_prefix}{euro}"
                    motorcycle_types.append({
                        'type_id': id, 'nb_seats': 1, 'length': 2.0, 'width': 1.0, 'pce': 1.0, 'mode': "motorcycle",
                        'hbefa_cat': "motorcycle", 'hbefa_tech': hbefa_tech, 'hbefa_size': hbefa_size, 'hbefa_emission': hbefa_emission,
                        'cnossos_cat': cnossos_cat
                    })
        elif size == "<=250cc":
            cnossos_cat = "4b"  # 4b for motorcycles >125cc in CNOSSOS-EU
            hbefa_size = "<=250cc"
            for hbefa_tech, hbefa_prefix in [("petrol (2S)", "MC-2S Euro-"), ("petrol (4S)", "MC 4S Euro-")]:
                for euro in ["0", "1", "2", "3", "4", "5", "6"]:
                    id = f"motorcycle_lte_250cc_{hbefa_tech[8:10]}_euro_{euro}_cnossos_{cnossos_cat}"
                    hbefa_emission = f"{hbefa_prefix}{euro}"
                    motorcycle_types.append({
                        'type_id': id, 'nb_seats': 1, 'length': 2.0, 'width': 1.0, 'pce': 1.0, 'mode': "motorcycle",
                        'hbefa_cat': "motorcycle", 'hbefa_tech': hbefa_tech, 'hbefa_size': hbefa_size, 'hbefa_emission': hbefa_emission,
                        'cnossos_cat': cnossos_cat
                    })
        elif size == ">250cc":
            cnossos_cat = "4b"  # 4b for motorcycles >125cc in CNOSSOS-EU
            hbefa_size = ">250cc"
            hbefa_tech = "petrol (4S)"
            hbefa_prefix = "MC 4S Euro-"
            for euro in ["0", "1", "2", "3", "4", "5", "6"]:
                id = f"motorcycle_gt_250cc_4S_euro_{euro}_cnossos_{cnossos_cat}"
                hbefa_emission = f"{hbefa_prefix}{euro}"
                motorcycle_types.append({
                    'type_id': id, 'nb_seats': 1, 'length': 2.0, 'width': 1.0, 'pce': 1.0, 'mode': "motorcycle",
                    'hbefa_cat': "motorcycle", 'hbefa_tech': hbefa_tech, 'hbefa_size': hbefa_size, 'hbefa_emission': hbefa_emission,
                    'cnossos_cat': cnossos_cat
                })

    df_types = pd.DataFrame.from_records(motorcycle_types)

    assert df_types['type_id'].is_unique, "Motorcycle type IDs are not unique !"
    # motorcycle_gt_250cc_4S_euro_3_cnossos_4b
    return df_types