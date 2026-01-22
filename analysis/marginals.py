import itertools
import numpy as np
import pandas as pd

AGE_CLASS_BOUNDS = [14, 29, 44, 59, 74, np.inf]
AGE_CLASS_LABELS = ["<15", "15-29", "30-44", "45-59", "60-74", "75+"]

HOUSEHOLD_SIZE_BOUNDS = [1, 3, np.inf]
HOUSEHOLD_SIZE_LABELS = ["1", "2-3", "4+"]

NUMBER_OF_CARS_BOUNDS = [0, 1, 2, np.inf]
NUMBER_OF_CARS_LABELS = ["0", "1", "2", "3+"]

NUMBER_OF_BICYCLES_BOUNDS = [0, 1, 2, np.inf]
NUMBER_OF_BICYCLES_LABELS = ["0", "1", "2", "3+"]

GENERAL_PERSON_MARGINALS = [("age_class",), ("sex",), ("employed",), ("studies",)]
GENERAL_HOUSEHOLD_MARGINALS = [("household_size_class",), ("number_of_cars_class",)]

CENSUS_PERSON_MARGINALS = GENERAL_PERSON_MARGINALS + [("socioprofessional_class",)]
CENSUS_HOUSEHOLD_MARGINALS = GENERAL_HOUSEHOLD_MARGINALS

HTS_PERSON_MARGINALS = GENERAL_PERSON_MARGINALS + [("has_license",), ("has_pt_subscription",)]
HTS_HOUSEHOLD_MARGINALS = GENERAL_HOUSEHOLD_MARGINALS + [("number_of_bikes_class",)]

SOCIOPROFESIONAL_CLASS_LABELS = [
    "???", "Agriculture", "Independent", "Science", "Intermediate", "Employee", "Worker", "Retired", "Other"
]

def prepare_classes(df):
    if "age" in df:
        df["age_class"] = np.digitize(df["age"], AGE_CLASS_BOUNDS, right = True)

    if "household_size" in df:
        df["household_size_class"] = np.digitize(df["household_size"], HOUSEHOLD_SIZE_BOUNDS, right = True)

    if "number_of_cars" in df:
        df["number_of_cars_class"] = np.digitize(df["number_of_cars"], NUMBER_OF_CARS_BOUNDS, right = True)

    if "number_of_bicycles" in df:
        df["number_of_bicycles_class"] = np.digitize(df["number_of_bicycles"], NUMBER_OF_BICYCLES_BOUNDS, right = True)

def cross(*marginals):
    result = []

    for items in itertools.product(*marginals):
        cross_marginal = []

        for item in items:
            cross_marginal += list(item)

        cross_marginal = np.unique(sorted(cross_marginal))
        cross_marginal = tuple(cross_marginal)

        result.append(cross_marginal)

    return list(set(result))

def combine(*marginals):
    result = []

    for item in marginals:
        result += item

    return list(set(result))

ALL_PERSON_MARGINALS = combine(CENSUS_PERSON_MARGINALS, HTS_PERSON_MARGINALS)
ALL_HOUSEHOLD_MARGINALS = combine(CENSUS_HOUSEHOLD_MARGINALS, HTS_HOUSEHOLD_MARGINALS)

SPATIAL_MARGINALS = [("departement_id",), ("commune_id",)]

ANALYSIS_PERSON_MARGINALS = combine(
    ALL_PERSON_MARGINALS, ALL_HOUSEHOLD_MARGINALS,
    cross(ALL_PERSON_MARGINALS, ALL_PERSON_MARGINALS),
    cross(ALL_HOUSEHOLD_MARGINALS, ALL_HOUSEHOLD_MARGINALS),
    cross(ALL_PERSON_MARGINALS, ALL_HOUSEHOLD_MARGINALS)
)

ANALYSIS_HOUSEHOLD_MARGINALS = combine(
    ALL_HOUSEHOLD_MARGINALS,
    cross(ALL_HOUSEHOLD_MARGINALS, ALL_HOUSEHOLD_MARGINALS)
)

SPATIAL_PERSON_MARGINALS = combine(
    SPATIAL_MARGINALS, cross(SPATIAL_MARGINALS, GENERAL_PERSON_MARGINALS)
)

SPATIAL_HOUSEHOLD_MARGINALS = combine(
    SPATIAL_MARGINALS, cross(SPATIAL_MARGINALS, GENERAL_HOUSEHOLD_MARGINALS)
)

TOTAL_MARGINAL = [tuple()]
