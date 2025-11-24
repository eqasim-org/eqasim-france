import numpy as np
import numpy.linalg as la

def check_feasibility(distances, direct_distance, consider_total_distance = True):
    return calculate_feasibility(distances, direct_distance, consider_total_distance) == 0.0

def calculate_feasibility(distances, direct_distance, consider_total_distance = True):
    total_distance = np.sum(distances)
    delta_distance = 0.0

    remaining_distance = total_distance - distances
    delta = max(distances - direct_distance - remaining_distance)

    if consider_total_distance:
        delta = max(delta, direct_distance - total_distance)

    return float(max(delta, 0))

class DiscretizationSolver:
    def solve(self, problem, locations):
        raise NotImplementedError()

class RelaxationSolver:
    def solve(self, problem, distances):
        raise NotImplementedError()

class DistanceSampler:
    def sample(self, problem):
        raise NotImplementedError()

class AssignmentObjective:
    def evaluate(self, problem, distance_result, relaxation_result, discretization_result):
        raise NotImplementedError()

class AssignmentSolver:
    def __init__(self, distance_sampler, relaxation_solver, discretization_solver, objective, maximum_iterations = 1000):
        self.maximum_iterations = maximum_iterations

        self.relaxation_solver = relaxation_solver
        self.distance_sampler = distance_sampler
        self.discretization_solver = discretization_solver
        self.objective = objective

    def solve(self, problem):
        best_result = None

        for assignment_iteration in range(self.maximum_iterations):
            distance_result = self.distance_sampler.sample(problem)

            relaxation_result = self.relaxation_solver.solve(problem, distance_result["distances"])
            discretization_result = self.discretization_solver.solve(problem, relaxation_result["locations"])

            assignment_result = self.objective.evaluate(problem, distance_result, relaxation_result, discretization_result)

            if best_result is None or assignment_result["objective"] < best_result["objective"]:
                best_result = assignment_result

                assignment_result["distance"] = distance_result
                assignment_result["relaxation"] = relaxation_result
                assignment_result["discretization"] = discretization_result
                assignment_result["iterations"] = assignment_iteration

            if best_result["valid"]:
                break

        return best_result

class GeneralRelaxationSolver(RelaxationSolver):
    def __init__(self, chain_solver, tail_solver = None, free_solver = None):
        self.chain_solver = chain_solver
        self.tail_solver = tail_solver
        self.free_solver = free_solver

    def solve(self, problem, distances):
        if problem["origin"] is None and problem["destination"] is None:
            return self.free_solver.solve(problem, distances)

        elif problem["origin"] is None or problem["destination"] is None:
            return self.tail_solver.solve(problem, distances)

        else:
            return self.chain_solver.solve(problem, distances)

def sample_tail(random, anchor, distances):
    angles = random.random_sample(len(distances)) * 2.0 * np.pi
    offsets = np.vstack([np.cos(angles), np.sin(angles)]).T * distances[:, np.newaxis]

    locations = [anchor]

    for k in range(len(distances)):
        locations.append(locations[-1] + offsets[k])

    return np.vstack(locations[1:])

class AngularTailSolver(RelaxationSolver):
    def __init__(self, random):
        self.random = random

    def solve(self, problem, distances):
        anchor, reverse = None, None

        if problem["origin"] is None:
            anchor = problem["destination"]
            reverse = False

        elif problem["destination"] is None:
            anchor = problem["origin"]
            reverse = True

        else:
            raise RuntimeError("Invalid chain for AngularTailSolver")

        locations = sample_tail(self.random, anchor, distances)
        if reverse: locations = locations[::-1,:]

        assert len(locations) == len(distances)
        return dict(valid = True, locations = locations, iterations = None)

class GravityChainSolver:
    def __init__(self, random, alpha = 0.3, eps = 1.0, maximum_iterations = 1000, lateral_deviation = None):
        self.alpha = alpha
        self.eps = eps
        self.maximum_iterations = maximum_iterations
        self.random = random
        self.lateral_deviation = lateral_deviation

    def solve_two_points(self, problem, origin, destination, distances, direction, direct_distance):
        if direct_distance == 0.0:
            location = origin + direction * distances[0]

            return dict(
                valid = distances[0] == distances[1],
                locations = location.reshape(-1, 2), iterations = None
            )

        elif direct_distance > np.sum(distances):
            ratio = 1.0

            if distances[0] > 0.0 or distances[1] > 0.0:
                ratio = distances[0] / np.sum(distances)

            location = origin + direction * ratio * direct_distance

            return dict(
                valid = False, locations = location.reshape(-1, 2), iterations = None
            )

        elif direct_distance < np.abs(distances[0] - distances[1]):
            ratio = 1.0

            if distances[0] > 0.0 or distances[1] > 0.0:
                ratio = distances[0] / np.sum(distances)

            maximum_distance = max(distances)
            location = origin + direction * ratio * maximum_distance

            return dict(
                valid = False, locations = location.reshape(-1, 2), iterations = None
            )

        else:
            A = 0.5 * ( distances[0]**2 - distances[1]**2 + direct_distance**2 ) / direct_distance
            H = np.sqrt(max(0, distances[0]**2 - A**2))
            r = self.random.random_sample()

            center = origin + direction * A
            offset = direction * H
            offset = np.array([offset[0,1], -offset[0,0]])

            location = center + (1.0 if r < 0.5 else -1.0) * offset

            return dict(
                valid = True, locations = location.reshape(-1, 2), iterations = None
            )

    def solve(self, problem, distances):
        origin, destination = problem["origin"], problem["destination"]

        if origin is None or destination is None:
            raise RuntimeError("Invalid chain for GravityChainSolver")

        # Prepare direction and normal direction
        direct_distance = la.norm(destination - origin)

        if direct_distance < 1e-12: # We have a zero direct distance, choose a direction randomly
            angle = self.random.random() * np.pi * 2.0

            direction = np.array([
                np.cos(angle), np.sin(angle)
            ]).reshape((1, 2))

        else:
            direction = (destination - origin) / direct_distance

        normal = np.array([direction[0,1], -direction[0,0]])

        # If we have only one variable point, take a short cut
        if problem["size"] == 1:
             return self.solve_two_points(problem, origin, destination, distances, direction, direct_distance)

        # Prepare initial locations
        if np.sum(distances) < 1e-12:
            shares = np.linspace(0, 1, len(distances) - 1)
        else:
            shares = np.cumsum(distances[:-1]) / np.sum(distances)

        locations = origin + direction * shares[:, np.newaxis] * direct_distance
        locations = np.vstack([origin, locations, destination])

        if not check_feasibility(distances, direct_distance):
            return dict( # We still return some locations although they may not be perfect
                valid = False, locations = locations[1:-1], iterations = None
            )

        # Add lateral devations
        lateral_deviation = self.lateral_deviation if not self.lateral_deviation is None else max(direct_distance, 1.0)
        locations[1:-1] += normal * 2.0 * (self.random.normal(size = len(distances) - 1)[:, np.newaxis] - 0.5) * lateral_deviation

        # Prepare gravity simulation
        valid = False

        origin_weights = np.ones((len(distances) - 1, 2))
        origin_weights[0,:] = 2.0

        destination_weights = np.ones((len(distances) - 1, 2))
        destination_weights[-1,:] = 2.0

        # Run gravity simulation
        for k in range(self.maximum_iterations):
            directions = locations[:-1] - locations[1:]
            lengths = la.norm(directions, axis = 1)

            offset = distances - lengths
            lengths[lengths < 1.0] = 1.0
            directions /= lengths[:, np.newaxis]

            if np.all(np.abs(offset) < self.eps): # Check if we have converged
                valid = True
                break

            # Apply adjustment to locations
            adjustment = np.zeros((len(distances) - 1, 2))
            adjustment -= 0.5 * self.alpha * offset[:-1, np.newaxis] * directions[:-1] * origin_weights
            adjustment += 0.5 * self.alpha * offset[1:, np.newaxis] * directions[1:] * destination_weights

            locations[1:-1] += adjustment

            if np.isnan(locations).any() or np.isinf(locations).any():
                raise RuntimeError("NaN/Inf value encountered during gravity simulation")

        return dict(
            valid = valid, locations = locations[1:-1], iterations = k
        )

class FeasibleDistanceSampler(DistanceSampler):
    def __init__(self, random, maximum_iterations = 1000):
        self.maximum_iterations = maximum_iterations
        self.random = random

    def sample_distances(self, problem):
        # Return distance chains per row
        raise NotImplementedError()

    def sample(self, problem):
        origin, destination = problem["origin"], problem["destination"]

        if origin is None and destination is None: # This is a free chain
            distances = self.sample_distances(problem)
            return dict(valid = True, distances = distances, iterations = None)

        elif origin is None: # This is a left tail
            distances = self.sample_distances(problem)
            return dict(valid = True, distances = distances, iterations = None)

        elif destination is None: # This is a right tail
            distances = self.sample_distances(problem)
            return dict(valid = True, distances = distances, iterations = None)

        direct_distance = la.norm(destination - origin, axis = 1)

        # One point and two trips
        if direct_distance < 1e-3 and problem["size"] == 1:
            distances = self.sample_distances(problem)
            distances = np.array([distances[0], distances[0]])

            return dict(valid = True, distances = distances, iterations = None)

        # This is the general case
        best_distances = None
        best_delta = None

        for k in range(self.maximum_iterations):
            distances = self.sample_distances(problem)
            delta = calculate_feasibility(distances, direct_distance)

            if best_delta is None or delta < best_delta:
                best_delta = delta
                best_distances = distances

                if delta == 0.0:
                    break

        return dict(
            valid = best_delta == 0.0,
            distances = best_distances,
            iterations = k
        )

class DiscretizationErrorObjective(AssignmentObjective):
    def __init__(self, thresholds):
        self.thresholds = thresholds

    def evaluate(self, problem, distance_result, relaxation_result, discretization_result):
        sampled_distances = distance_result["distances"]

        discretized_locations = []
        if not problem["origin"] is None: discretized_locations.append(problem["origin"])
        discretized_locations.append(discretization_result["locations"])
        if not problem["destination"] is None: discretized_locations.append(problem["destination"])
        discretized_locations = np.vstack(discretized_locations)

        discretized_distances = la.norm(discretized_locations[:-1] - discretized_locations[1:], axis = 1)
        discretization_error = np.abs(sampled_distances - discretized_distances)

        objective = 0.0
        for error, mode in zip(discretization_error, problem["modes"]):
            target_error = self.thresholds[mode]
            excess_error = max(0.0, error - target_error )
            objective = max(objective, excess_error)

        valid = objective == 0.0
        valid &= distance_result["valid"]
        valid &= relaxation_result["valid"]
        valid &= discretization_result["valid"]

        return dict(valid = valid, objective = objective)
