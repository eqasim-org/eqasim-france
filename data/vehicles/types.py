import pandas as pd

"""
This stage creates the various type of vehicles needed for the simulation with HBEFA emissions
"""

HBEFA_TECH = ["petrol", "diesel"]
HBEFA_EURO = ["1", "2", "3", "4", "5", "6ab", "6c", "6d"]


def configure(context):
    pass


def execute(context):

    vehicle_types = [
        {
            "type_id": "default_car",
            "nb_seats": 4,
            "length": 5.0,
            "width": 1.0,
            "pce": 1.0,
            "mode": "car",
            "hbefa_cat": "PASSENGER_CAR",
            "hbefa_tech": "average",
            "hbefa_size": "average",
            "hbefa_emission": "average",
        }
    ]

    for technology in HBEFA_TECH:
        for euro in HBEFA_EURO:
            tech = technology

            id = "car_%s_%s" % (technology, euro)

            if technology == "diesel" and euro in ["2", "3"]:
                euro += " (DPF)"

            size = ">=2L" if technology == "petrol" else "<1,4L"

            if technology == "petrol":
                tech += " (4S)"

            emission = "PC %s Euro-%s" % (tech, euro)

            vehicle_types.append(
                {
                    "type_id": id,
                    "length": 7.5,
                    "width": 1.0,
                    "hbefa_cat": "PASSENGER_CAR",
                    "hbefa_tech": tech,
                    "hbefa_size": size,
                    "hbefa_emission": emission,
                }
            )

    df_types = pd.DataFrame.from_records(vehicle_types)
    return df_types
