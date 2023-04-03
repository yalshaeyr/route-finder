# Import necessary modules to solve the traveling salesman problem (TSP) 
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Holds the route and objective of a TSP problem 
class Solution:
    def __init__(self, route, objective_value):
        self.route = route
        self.objective_value = objective_value

# Define the class which solves the traveling salesman problem 
class TSP:
    # Initialise input variables 
    def __init__(self, distance_matrix, nodes_to_visit):
        self.distance_matrix = distance_matrix
        self.nodes_to_visit = nodes_to_visit
        self.num_nodes = len(nodes_to_visit)
        # Create a routing index manager and routing model for the problem
        # The index manager keeps a map of the indices of the nodes used 
        # in the routing model and the indices of the nodes in the TSP        
        self.manager = pywrapcp.RoutingIndexManager(self.num_nodes, 1, 0)
        # The routing model itself will consider the TSP as a graph problem
        # and use an algorithm to optimise the route 
        self.routing = pywrapcp.RoutingModel(self.manager)
        # Set up a distance callback for the routing model. This simply 
        # provides the distance between two nodes 
        self.setup_distance_callback()
        self.routing.SetArcCostEvaluatorOfAllVehicles(self.distance_callback_index)
        # Set search parameters for the routing model
        self.search_parameters = pywrapcp.DefaultRoutingSearchParameters() # should be suitable for most routes 
        # The first strategy should be to find the cheapest path 
        self.search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Define a distance callback function for the routing model
    # This calculates the distance between two nodes using a distance matrix    
    def setup_distance_callback(self):
        def distance_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            return self.distance_matrix[self.nodes_to_visit[from_node]][self.nodes_to_visit[to_node]]

        self.distance_callback = distance_callback
        self.distance_callback_index = self.routing.RegisterTransitCallback(self.distance_callback)
    
    # Solve the TSP problem and return a Solution object
    def solve(self):
        solution = self.routing.SolveWithParameters(self.search_parameters)
        if not solution:
            return None

        return self.get_solution_object(solution)
    
    # Create a Solution object from the solution returned by the routing model
    def get_solution_object(self, solution):
        route = [] # Start with an empty route 
        index = self.routing.Start(0) #start at the root node 
        # While the routing isn't finished 
        while not self.routing.IsEnd(index):
            # Add current node 
            route.append(self.nodes_to_visit[self.manager.IndexToNode(index)])
            # Get the next optimal node 
            index = solution.Value(self.routing.NextVar(index))
        # Add the last node 
        route.append(self.nodes_to_visit[self.manager.IndexToNode(index)])

        return Solution(route, solution.ObjectiveValue())