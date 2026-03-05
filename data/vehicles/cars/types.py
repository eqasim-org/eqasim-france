import pandas as pd

"""
This stage creates the various type of vehicles needed for the simulation with HBEFA emissions
"""

HBEFA_TECH = ['petrol', 'diesel']
HBEFA_EURO = ['1', '2', '3', '4', '5', '6ab', '6c', '6d']

def configure(context):
    pass

def execute(context):

    default_car_type = {
        'type_id': 'default_car', 'nb_seats': 4, 'length': 5.0, 'width': 1.0, 'pce': 1.0, 'mode': "car",
        'hbefa_cat': "pass. car", 'hbefa_tech': "average", 'hbefa_size': "average", 'hbefa_emission': "average",
        'cnossos_cat': "1"
    }
    car_types = [default_car_type]

    for technology in HBEFA_TECH:
        for euro in HBEFA_EURO:
            tech = technology

            id = "car_%s_%s" % (technology, euro)

            size = "not specified"

            if technology == "petrol":
                tech += " (4S)"

            concept_tech = technology[0].upper() # first letter upped : "P" for petrol, "D" for diesel
            em_concept = "PC %s Euro-%s" % (concept_tech, euro)

            car_types.append({
                'type_id': id, 'nb_seats': 4, 'length': 5.0, 'width': 1.0, 'pce': 1.0, 'mode': "car",
                'hbefa_cat': "pass. car", 'hbefa_tech': tech, 'hbefa_size': size, 'hbefa_emission': em_concept,
                'cnossos_cat': "1"
            })

    df_types = pd.DataFrame.from_records(car_types)
    return df_types