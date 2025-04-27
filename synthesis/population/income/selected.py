
def configure(context):
    method = context.config("income_assignation_method", "uniform")

    if method == "uniform":
        context.stage("synthesis.population.income.uniform", alias = "income")
    elif method == "bhepop2":
        context.stage("synthesis.population.income.bhepop2", alias = "income")
    else:
        raise RuntimeError("Unknown income assignation method : %s" % method)

def execute(context):
    return context.stage("income")

