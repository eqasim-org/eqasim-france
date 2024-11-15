import pandas as pd
import re

CHAIN_LENGTH_LIMIT = 10
CHAIN_TOP_K = 50

CHAIN_MARGINALS = [
    ("chain", "age_class"),
    ("chain", "sex"),
    ("chain_length_class", "age_class"),
    ("chain_length_class", "sex"),
    ("chain",),
    ("chain_length_class",),
    ("age_range", "sex", "chain"),
    ("age_range", "sex", "chain_length_class"),
]

PURPOSE_MAPPING = {
    "home": "h",
    "work": "w",
    "education": "e",
    "shop": "s",
    "leisure": "l",
    "other": "o",
}


def aggregate_chains(df_chains):
    current_person_id = None
    current_chain = None
    records = []

    for person_id, purpose in zip(
        df_chains["person_id"].values, df_chains["purpose"].values
    ):
        if not person_id == current_person_id:
            if not current_person_id is None:
                records.append((current_person_id, current_chain))

            current_chain = PURPOSE_MAPPING[purpose]
            current_person_id = person_id
        else:
            current_chain += PURPOSE_MAPPING[purpose]

    records.append((current_person_id, current_chain))

    df_chains = pd.DataFrame.from_records(records, columns=["person_id", "chain"])

    # df_chains["chain"] = df_chains["chain"].apply(lambda x: re.sub(r"w+", "w", x))
    # df_chains["chain"] = df_chains["chain"].apply(lambda x: re.sub(r"e+", "e", x))
    # df_chains["chain"] = df_chains["chain"].apply(lambda x: re.sub(r"h+", "h", x))

    df_chains["chain_length"] = df_chains["chain"].str.len()

    return df_chains
