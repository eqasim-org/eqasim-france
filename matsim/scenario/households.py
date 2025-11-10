import io, gzip

import numpy as np
import pandas as pd

import matsim.writers as writers

def configure(context):
    context.stage("synthesis.population.enriched")

FIELDS = ["household_id", "person_id", "household_income", "car_availability", "bicycle_availability", "census_household_id"]

def add_household(writer, household, member_ids):
    writer.start_household(household[FIELDS.index("household_id")])
    writer.add_members(member_ids)

    writer.start_attributes()
    writer.add_attribute("carAvailability", "java.lang.String", household[FIELDS.index("car_availability")])
    writer.add_attribute("bicycleAvailability", "java.lang.String", household[FIELDS.index("bicycle_availability")])
    writer.add_attribute("household_income", "java.lang.Double", household[FIELDS.index("household_income")])
    writer.add_attribute("censusId", "java.lang.Long", household[FIELDS.index("census_household_id")])
    writer.end_attributes()

    writer.end_household()

def execute(context):
    output_path = "%s/households.xml.gz" % context.path()

    df_persons = context.stage("synthesis.population.enriched")
    df_persons = df_persons.sort_values(by = ["household_id", "person_id"])
    df_persons = df_persons[FIELDS]

    current_members = []
    current_household_id = None
    current_household = None

    with gzip.open(output_path, 'wb+') as writer:
        with io.BufferedWriter(writer, buffer_size = 2 * 1024**3) as writer:
            writer = writers.HouseholdsWriter(writer)
            writer.start_households()

            with context.progress(total = len(df_persons), label = "Writing households ...") as progress:
                for item in df_persons.itertuples(index = False):
                    if current_household_id != item[FIELDS.index("household_id")]:
                        if not current_household_id is None:
                            add_household(writer, current_household, current_members)

                        current_household = item
                        current_household_id = item[FIELDS.index("household_id")]
                        current_members = [item[FIELDS.index("person_id")]]
                    else:
                        current_members.append(item[FIELDS.index("person_id")])

                    progress.update()

            if not current_household_id is None:
                add_household(writer, current_household, current_members)

            writer.end_households()

    return "households.xml.gz"
