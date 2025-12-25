import synthesis.population.spatial.secondary.rda as rda
import sklearn.neighbors
import numpy as np

class CustomDistanceSampler(rda.FeasibleDistanceSampler):
    def __init__(self, random, distributions, maximum_iterations = 1000):
        rda.FeasibleDistanceSampler.__init__(self, random = random, maximum_iterations = maximum_iterations)

        self.random = random
        self.distributions = distributions

    def sample_distances(self, problem):
        distances = np.zeros((len(problem["modes"])))

        for index, (mode, travel_time) in enumerate(zip(problem["modes"], problem["travel_times"])):
            mode_distribution = self.distributions[mode]

            bound_index = np.count_nonzero(travel_time > mode_distribution["bounds"])
            mode_distribution = mode_distribution["distributions"][bound_index]

            distances[index] = mode_distribution["values"][
                np.count_nonzero(self.random.random() > mode_distribution["cdf"])
            ]

        return distances

class CandidateIndex:
    def __init__(self, data):
        self.data = data
        self.indices = {}

        for purpose, data in self.data.items():
            print("Constructing spatial index for %s ..." % purpose)
            self.indices[purpose] = sklearn.neighbors.KDTree(data["locations"])

    def query(self, purpose, location):
        index = self.indices[purpose].query(location.reshape(1, -1), return_distance = False)[0][0]
        identifier = self.data[purpose]["identifiers"][index]
        location = self.data[purpose]["locations"][index]
        return identifier, location

    def sample(self, purpose, random):
        index = random.integers(0, len(self.data[purpose]["locations"]))
        identifier = self.data[purpose]["identifiers"][index]
        location = self.data[purpose]["locations"][index]
        return identifier, location

class CustomDiscretizationSolver(rda.DiscretizationSolver):
    def __init__(self, index):
        self.index = index

    def solve(self, problem, locations):
        discretized_locations = []
        discretized_identifiers = []

        for location, purpose in zip(locations, problem["purposes"]):
            identifier, location = self.index.query(purpose, location.reshape(1, -1))

            discretized_identifiers.append(identifier)
            discretized_locations.append(location)

        assert len(discretized_locations) == problem["size"]

        return dict(
            valid = True, locations = np.vstack(discretized_locations), identifiers = discretized_identifiers
        )

class CustomFreeChainSolver(rda.RelaxationSolver):
    def __init__(self, random, index):
        self.random = random
        self.index = index

    def solve(self, problem, distances):
        identifier, anchor = self.index.sample(problem["purposes"][0], self.random)
        locations = rda.sample_tail(self.random, anchor, distances)
        locations = np.vstack((anchor, locations))

        assert len(locations) == len(distances) + 1
        return dict(valid = True, locations = locations)
