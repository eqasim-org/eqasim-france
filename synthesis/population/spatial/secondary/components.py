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
                np.count_nonzero(self.random.random_sample() > mode_distribution["cdf"])
            ]

        return distances

class CandidateIndex:
    def __init__(self, data,random):
        self.data = data
        self.indices = {}
        self.random = random

        for purpose, data in self.data.items():
            print("Constructing spatial index for %s ..." % purpose)
            self.indices[purpose] = sklearn.neighbors.KDTree(data["locations"])

    def query(self, purpose, location):
        index = self.indices[purpose].query(location.reshape(1, -1),k=20, return_distance = False)[0]#[0]
        if purpose == "shop" : # choose location while taking count of weight of closest locations
            weight= self.data[purpose]["weight"][index]
            weight = weight /np.sum(weight,dtype=float)
            rng = np.random.default_rng(self.random)
            index = rng.choice(index,p=weight)
        else :
            index = index[0]
        identifier = self.data[purpose]["identifiers"][index]
        location = self.data[purpose]["locations"][index]
        type_act = self.data[purpose]["type_act"][index]
        return identifier, location,type_act

    def sample(self, purpose, random):
        index = random.randint(0, len(self.data[purpose]["locations"]))
        identifier = self.data[purpose]["identifiers"][index]
        location = self.data[purpose]["locations"][index]
        type_act = self.data[purpose]["type_act"][index]
        return identifier, location,type_act

class CustomDiscretizationSolver(rda.DiscretizationSolver):
    def __init__(self, index):
        self.index = index

    def solve(self, problem, locations):
        discretized_locations = []
        discretized_identifiers = []
        discretized_type_acts = []

        for location, purpose in zip(locations, problem["purposes"]):
            identifier, location,type_act = self.index.query(purpose, location.reshape(1, -1))

            discretized_identifiers.append(identifier)
            discretized_locations.append(location)
            discretized_type_acts.append(type_act)

        assert len(discretized_locations) == problem["size"]

        return dict(
            valid = True, locations = np.vstack(discretized_locations), identifiers = discretized_identifiers,type_acts= discretized_type_acts
        )

class CustomFreeChainSolver(rda.RelaxationSolver):
    def __init__(self, random, index):
        self.random = random
        self.index = index

    def solve(self, problem, distances):
        identifier, anchor,type_act = self.index.sample(problem["purposes"][0], self.random)
        locations = rda.sample_tail(self.random, anchor, distances)
        locations = np.vstack((anchor, locations))

        assert len(locations) == len(distances) + 1
        return dict(valid = True, locations = locations, iterations = None)
