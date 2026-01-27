import numpy as np
import pandas as pd
import multiprocessing as mp
import shapely.geometry as geo
import geopandas as gpd

from synthesis.population.spatial.secondary.problems import find_assignment_problems

def configure(context):
    context.stage("synthesis.population.trips")

    context.stage("synthesis.population.sampled")
    context.stage("synthesis.population.spatial.home.locations")
    context.stage("synthesis.population.spatial.primary.locations")

    context.stage("synthesis.population.spatial.secondary.distance_distributions")
    context.stage("synthesis.locations.secondary")

    context.config("random_seed")
    context.config("processes", volatile = True)

    context.config("secloc_maximum_iterations", np.inf)

def prepare_locations(context):
    # Load persons and their primary locations
    df_home = context.stage("synthesis.population.spatial.home.locations")
    df_work, df_education = context.stage("synthesis.population.spatial.primary.locations")
    crs = df_home.crs

    df_home = df_home.rename(columns = { "geometry": "home" })
    df_work = df_work.rename(columns = { "geometry": "work" })
    df_education = df_education.rename(columns = { "geometry": "education" })

    df_locations = context.stage("synthesis.population.sampled")[["person_id", "household_id"]]
    df_locations = pd.merge(df_locations, df_home[["household_id", "home"]], how = "left", on = "household_id")
    df_locations = pd.merge(df_locations, df_work[["person_id", "work"]], how = "left", on = "person_id")
    df_locations = pd.merge(df_locations, df_education[["person_id", "education"]], how = "left", on = "person_id")

    return df_locations[["person_id", "home", "work", "education"]].sort_values(by = "person_id"), crs

def prepare_destinations(context):
    df_locations = context.stage("synthesis.locations.secondary")

    identifiers = df_locations["location_id"].values
    locations = np.vstack(df_locations["geometry"].apply(lambda x: np.array([x.x, x.y])).values)

    data = {}

    for purpose in ("shop", "leisure", "other"):
        f = df_locations["offers_%s" % purpose].values

        data[purpose] = dict(
            identifiers = identifiers[f],
            locations = locations[f]
        )

    return data

def resample_cdf(cdf, factor):
    if factor >= 0.0:
        cdf = cdf * (1.0 + factor * np.arange(1, len(cdf) + 1) / len(cdf))
    else:
        cdf = cdf * (1.0 + abs(factor) - abs(factor) * np.arange(1, len(cdf) + 1) / len(cdf))

    cdf /= cdf[-1]
    return cdf

def resample_distributions(distributions, factors):
    for mode, mode_distributions in distributions.items():
        for distribution in mode_distributions["distributions"]:
            distribution["cdf"] = resample_cdf(distribution["cdf"], factors[mode])

from synthesis.population.spatial.secondary.rda import AssignmentSolver, DiscretizationErrorObjective, GravityChainSolver, AngularTailSolver, GeneralRelaxationSolver
from synthesis.population.spatial.secondary.components import CustomDistanceSampler, CustomDiscretizationSolver, CandidateIndex, CustomFreeChainSolver

def execute(context):
    # Load trips and primary locations
    df_trips = context.stage("synthesis.population.trips").sort_values(by = ["person_id", "trip_index"])
    df_trips["travel_time"] = df_trips["arrival_time"] - df_trips["departure_time"]
    df_primary, crs = prepare_locations(context)

    # Prepare data
    distance_distributions = context.stage("synthesis.population.spatial.secondary.distance_distributions")
    destinations = prepare_destinations(context)

    # Resampling for calibration
    resample_distributions(distance_distributions, dict(
        car = 0.0, car_passenger = 0.1, pt = 0.5, bike = 0.0, walk = -0.5
    ))

    # Segment into subsamples
    processes = context.config("processes")

    unique_person_ids = df_trips["person_id"].unique()
    number_of_persons = len(unique_person_ids)
    unique_person_ids = np.array_split(unique_person_ids, processes)

    random = np.random.default_rng(context.config("random_seed"))
    random_seeds = random.integers(10000, size = processes)

    # Create batch problems for parallelization
    batches = []

    for index in range(processes):
        batches.append((
            df_trips[df_trips["person_id"].isin(unique_person_ids[index])],
            df_primary[df_primary["person_id"].isin(unique_person_ids[index])],
            random_seeds[index], crs
        ))

    # Run algorithm in parallel
    with context.progress(label = "Assigning secondary locations to persons", total = number_of_persons):
        with context.parallel(processes = processes, data = dict(
            distance_distributions = distance_distributions,
            destinations = destinations
        )) as parallel:
            df_locations, df_convergence = [], []

            for df_locations_item, df_convergence_item in parallel.imap_unordered(process, batches):
                df_locations.append(df_locations_item)
                df_convergence.append(df_convergence_item)

    df_locations = pd.concat(df_locations).sort_values(by = ["person_id", "activity_index"])
    df_convergence = pd.concat(df_convergence)

    print("Success rate:", df_convergence["valid"].mean())

    return df_locations, df_convergence

def process(context, arguments):
  df_trips, df_primary, random_seed, crs = arguments

  # Set up RNG
  random = np.random.default_rng(random_seed)
  maximum_iterations = context.config("secloc_maximum_iterations")

  # Set up discretization solver
  destinations = context.data("destinations")
  candidate_index = CandidateIndex(destinations)
  discretization_solver = CustomDiscretizationSolver(candidate_index)

  # Set up distance sampler
  distance_distributions = context.data("distance_distributions")
  distance_sampler = CustomDistanceSampler(
        maximum_iterations = min(1000, maximum_iterations),
        random = random,
        distributions = distance_distributions)

  # Set up relaxation solver; currently, we do not consider tail problems.
  chain_solver = GravityChainSolver(
    random = random, eps = 10.0, lateral_deviation = 10.0, alpha = 0.1,
    maximum_iterations = min(1000, maximum_iterations)
    )

  tail_solver = AngularTailSolver(random = random)
  free_solver = CustomFreeChainSolver(random, candidate_index)

  relaxation_solver = GeneralRelaxationSolver(chain_solver, tail_solver, free_solver)

  # Set up assignment solver
  thresholds = dict(
    car = 200.0, car_passenger = 200.0, pt = 200.0,
    bike = 100.0, walk = 100.0
  )

  assignment_objective = DiscretizationErrorObjective(thresholds = thresholds)
  assignment_solver = AssignmentSolver(
      distance_sampler = distance_sampler,
      relaxation_solver = relaxation_solver,
      discretization_solver = discretization_solver,
      objective = assignment_objective,
      maximum_iterations = min(20, maximum_iterations)
      )

  df_locations = []
  df_convergence = []

  last_person_id = None

  for problem in find_assignment_problems(df_trips, df_primary):
      result = assignment_solver.solve(problem)

      starting_activity_index = problem["activity_index"]

      for index, (identifier, location) in enumerate(zip(result["discretization"]["identifiers"], result["discretization"]["locations"])):
          df_locations.append((
              problem["person_id"], starting_activity_index + index, identifier, geo.Point(location)
          ))

      df_convergence.append((
          result["valid"], problem["size"]
      ))

      if problem["person_id"] != last_person_id:
          last_person_id = problem["person_id"]
          context.progress.update()

  df_locations = pd.DataFrame.from_records(df_locations, columns = ["person_id", "activity_index", "location_id", "geometry"])
  df_locations = gpd.GeoDataFrame(df_locations, crs = crs)
  assert not df_locations["geometry"].isna().any()

  df_convergence = pd.DataFrame.from_records(df_convergence, columns = ["valid", "size"])
  return df_locations, df_convergence
