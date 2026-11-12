import synthesis.population.spatial.secondary.rda as rda
import sklearn.neighbors
import numpy as np
import numpy.linalg as la

class CustomDistanceSampler(rda.FeasibleDistanceSampler):
    def __init__(self, random, distributions, maximum_iterations = 1000):
        rda.FeasibleDistanceSampler.__init__(self, random = random, maximum_iterations = maximum_iterations)

        self.random = random
        self.distributions = distributions

        # Flatten all distributions into two arrays (cdf and values) such that
        # the compiled sampling kernel can access them. For each mode, we keep
        # track where the distribution of each travel time bin starts and ends.
        cdf, values, offset = [], [], 0
        self.slices = {}

        for mode, mode_distribution in distributions.items():
            self.slices[mode] = []

            for distribution in mode_distribution["distributions"]:
                assert len(distribution["cdf"]) == len(distribution["values"])

                cdf.append(distribution["cdf"])
                values.append(distribution["values"])

                self.slices[mode].append((offset, offset + len(distribution["cdf"])))
                offset += len(distribution["cdf"])

        self.cdf = np.ascontiguousarray(np.concatenate(cdf), dtype = np.float64)
        self.values = np.ascontiguousarray(np.concatenate(values), dtype = np.float64)

    def _get_slices(self, problem):
        # Find the relevant distribution for each trip of the problem. This is
        # only done once per problem, as the solver samples many times.
        if not "_distance_slices" in problem:
            starts = np.empty(len(problem["modes"]), dtype = np.int64)
            ends = np.empty(len(problem["modes"]), dtype = np.int64)

            for index, (mode, travel_time) in enumerate(zip(problem["modes"], problem["travel_times"])):
                bound_index = np.count_nonzero(travel_time > self.distributions[mode]["bounds"])
                starts[index], ends[index] = self.slices[mode][bound_index]

            problem["_distance_slices"] = (starts, ends)

        return problem["_distance_slices"]

    def sample_distances(self, problem):
        starts, ends = self._get_slices(problem)
        distances = np.empty(len(starts))
        rda._sample_distances(self.random, self.cdf, self.values, starts, ends, distances)
        return distances

    def sample(self, problem):
        origin, destination = problem["origin"], problem["destination"]

        # Free chains, tails, and round trips with one activity are handled by
        # the generic implementation (one draw only)
        if origin is None or destination is None:
            return rda.FeasibleDistanceSampler.sample(self, problem)

        direct_distance = la.norm(destination - origin, axis = 1)[0]

        if direct_distance < 1e-3 and problem["size"] == 1:
            return rda.FeasibleDistanceSampler.sample(self, problem)

        # This is the general case
        starts, ends = self._get_slices(problem)

        distances, delta, iterations = rda._sample_feasible_distances(
            self.random, self.cdf, self.values, starts, ends,
            direct_distance, int(self.maximum_iterations))

        return dict(valid = delta == 0.0, distances = distances, iterations = iterations)

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
    def __init__(self, index, random, escort_activities, escort_weights):
        self.index = index
        self.random = random
        self.escort_activities = np.array(escort_activities)
        self.escort_probs = np.array(escort_weights) / np.sum(escort_weights)

    def solve(self, problem, locations):
        discretized_locations = []
        discretized_identifiers = []

        for location, purpose in zip(locations, problem["purposes"]):
            if purpose == "escort":
                loc_purpose = str(self.random.choice(self.escort_activities, p=self.escort_probs))
            else:
                loc_purpose = purpose
            identifier, location = self.index.query(loc_purpose, location.reshape(1, -1))

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
        return dict(valid = True, locations = locations, iterations = None)
