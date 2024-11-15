def create_labels(df, marginals):
    labels = df.apply(
        lambda x: "%s %s"
        % (
            marginals[x["marginal"]]["category_label"],
            marginals[x["marginal"]]["label"],
        ),
        axis=1,
    )

    labels = labels.str.replace("Number of", "No.")
    labels = labels.str.replace("Socioprof. Cat.", "SC")

    return labels.values


def filter_marginals(df, marginal_level, marginals, blacklist=set()):
    df = df[df["marginal_level"] == marginal_level]
    df = df[df["marginal"].isin(marginals.keys())]
    df = df[~df["marginal"].isin(blacklist)]
    return df
