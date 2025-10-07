import numpy as np
import numpy.linalg as la

class ForceField:
    def __init__(self, grid_params, force_field, mean = 1.0, ceiling = 10.0):
        self.xmin = grid_params["xmin"]
        self.ymin = grid_params["ymin"]

        self.nx = grid_params["nx"]
        self.ny = grid_params["ny"]

        self.cell_size = grid_params["cell_size"]

        self.field = force_field / la.norm(force_field, axis = -1).mean() * mean

        norm = la.norm(self.field, axis = -1)
        self.field[norm > ceiling] = self.field[norm > ceiling] / norm[norm > ceiling, np.newaxis] * ceiling

    def calculate_force(self, x, y):
        xi = int(np.floor((x - self.xmin) / self.cell_size))
        yi = int(np.floor((y - self.ymin) / self.cell_size))

        if xi < 0 or xi + 1 >= self.nx or yi < 0 or yi + 1 >= self.ny:
            return np.array([0, 0])
        
        tx = (x - (self.xmin + xi * self.cell_size)) / self.cell_size
        ty = (y - (self.ymin + yi * self.cell_size)) / self.cell_size
        
        return tx * ty * self.field[xi, yi, :] \
            + tx * (1 - ty) * self.field[xi, yi + 1, :] \
            + (1 - tx) * ty * self.field[xi + 1, yi, :] \
            + (1 - tx) * (1 - ty) * self.field[xi + 1, yi + 1, :]

class ForceFieldChainSolver:
    def __init__(self, grid_parameters, force_fields, random, alpha = 0.3, ff_mean = 30., ff_ceiling = 60., maximum_iterations = 1000):
        self.maximum_iterations = maximum_iterations
        self.eps = 250. # Should be cell size
        self.eps_iter = 50 # Must be chosen so that ff_mean * eps_iter >> eps
        self.alpha = alpha
        self.random = random
        self.force_fields = {}

        for activitiy_type in force_fields:
            self.force_fields[activitiy_type] = ForceField(
                grid_parameters, force_fields[activitiy_type], mean = ff_mean, ceiling = ff_ceiling)

    def solve(self, problem, distances):
        origin, destination = problem["origin"], problem["destination"]

        if origin is None or destination is None:
            raise RuntimeError("Invalid chain for ForceFieldChainSolver")

        direct_distance = la.norm(destination - origin)
        locations = np.zeros((problem["size"], 2))

        if direct_distance < 1e-12:
            locations = np.tile(origin, (problem["size"], 1))
        else:
            direction = (destination - origin) / direct_distance

            if np.sum(distances) < 1e-12:
                locations = origin + direction * np.linspace(0, direct_distance, problem["size"], endpoint = False)[:, np.newaxis]
            else:
                shares = np.cumsum(distances[:-1]) / np.sum(distances)
                locations = origin + direction * shares[:, np.newaxis] * direct_distance

        if np.sum(distances) < direct_distance:
            return dict(valid = False, locations = locations, iterations = None)

        origin_weights = np.ones((problem["size"], 2))
        origin_weights[0,:] = 2.0

        destination_weights = np.ones((problem["size"], 2))
        destination_weights[-1,:] = 2.0

        field_forces = None
        current_distances = None

        stored_locations = np.zeros((self.eps_iter, problem["size"], 2))

        for k in range(self.maximum_iterations):
            stored_locations[k % self.eps_iter, :, :] = locations

            deltas = np.vstack([locations[0] - origin, locations[1:] - locations[:-1], destination - locations[-1]])
            current_distances = la.norm(deltas, axis=1)
            if np.isnan(current_distances).any():
                raise RuntimeError("NaN value")

            random_angles = self.random.random(problem["size"] + 1) * np.pi * 2.0
            directions = np.stack([np.cos(random_angles), np.sin(random_angles)], axis=1)
            directions[current_distances > 0.0, :] = deltas[current_distances > 0.0, :] / current_distances[current_distances > 0.0, np.newaxis]

            spring_forces_a = .5 * self.alpha * (directions * (distances - current_distances)[:, np.newaxis])[:-1] * origin_weights
            spring_forces_b = .5 * self.alpha * (directions * (current_distances - distances)[:, np.newaxis])[1:] * destination_weights
            field_forces = np.zeros((problem["size"], 2))
            for i, purpose in enumerate(problem["purposes"]):
                if purpose in self.force_fields:
                    field_forces[i, :] = self.force_fields[purpose].calculate_force(locations[i, 0], locations[i, 1])

            adjustments = spring_forces_a + spring_forces_b + field_forces
            locations += adjustments

            if k >= self.eps_iter:
                if np.all(la.norm(locations - stored_locations[(k + 1) % self.eps_iter, :, :], axis=1) < self.eps):
                    break

        return dict(valid = True, locations = locations, iterations = k)
