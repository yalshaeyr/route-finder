# Import required modules 
import pandas as pd
import googlemaps
import os
import pickle
import itertools
import datetime
from solution_class import *
from gmplot import gmplot

# Function to read CSV files
def read_csv_files(worker_file, job_file):
    try:
        workers = pd.read_csv(worker_file, names=["worker_name", "number_of_jobs"], skiprows=1)
        jobs = pd.read_csv(job_file, names=["job_ID", "address"], skiprows=1)
    except Exception as e:
        print("Error reading CSV files:", e)
        exit()
    return workers, jobs

# Function to calculate the distance matrix
def calculate_distance_matrix(jobs, distance_matrix_file):
    if os.path.exists(distance_matrix_file):
        with open(distance_matrix_file, "rb") as f:
            distance_matrix = pickle.load(f)
    else:
        gmaps = googlemaps.Client(key='')
        addresses = jobs["address"].values
        distance_matrix = gmaps.distance_matrix(addresses, addresses, units="metric")
        with open(distance_matrix_file, "wb") as f:
            pickle.dump(distance_matrix, f)

    distance_matrix = [
        [
            leg['distance']['value']
            for leg in row['elements']
        ]
        for row in distance_matrix['rows']
    ]
    return distance_matrix

# Function to print the solution
def print_solution(worker, assigned_nodes, distance_matrix, jobs):
    print(f"Worker: {worker['worker_name']}")
    route_distance = 0
    for i in range(len(assigned_nodes) - 1):
        from_node, to_node = assigned_nodes[i], assigned_nodes[i + 1]
        route_distance += distance_matrix[from_node][to_node]
        print(f"{jobs['address'].iloc[from_node]} -> ", end="")
    print(jobs['address'].iloc[assigned_nodes[-1]])
    print(f"Distance: {route_distance}\n")

# Function to calculate the shortest route for a worker
def shortest_route_for_worker(distance_matrix, worker, visited_nodes):
    depot = 0
    all_nodes = set(range(len(distance_matrix)))
    unvisited_nodes = all_nodes - visited_nodes
    num_required_nodes = worker["number_of_jobs"]

    if len(unvisited_nodes) < num_required_nodes:
        return None

    min_distance = float("inf")
    min_route = None

    for combination in itertools.combinations(unvisited_nodes, num_required_nodes):
        nodes_to_visit = [depot] + list(combination) + [depot]
        tsp = TSP(distance_matrix, nodes_to_visit)
        solution = tsp.solve()

        if solution and solution.objective_value < min_distance:
            min_distance = solution.objective_value
            min_route = solution.route

    return min_route

# Assigns jobs to each worker by finding the shortest route for each worker 
def assign_jobs_to_workers(workers, distance_matrix):
    # Use the original distance matrix without removing the first row and column
    modified_distance_matrix = distance_matrix

    # Create a list to store the assigned nodes for each worker
    assigned_nodes_for_workers = [set() for _ in range(len(workers))]

    # Assign the minimum number of jobs for each worker
    for worker_idx, worker in workers.iterrows():
        num_required_nodes = worker["number_of_jobs"]

        for _ in range(num_required_nodes):
            min_distance = float("inf")
            min_route = None
            min_node = None

            for node in range(len(distance_matrix)):
                if node in set.union(*assigned_nodes_for_workers):
                    continue

                current_route = shortest_route_for_worker(modified_distance_matrix, worker, assigned_nodes_for_workers[worker_idx] | {node})

                if current_route is not None:
                    adjusted_route = [n - 1 if n != 0 else n for n in current_route]
                    current_distance = sum(modified_distance_matrix[adjusted_route[i]][adjusted_route[i + 1]] for i in range(len(adjusted_route) - 1))

                    if current_distance < min_distance:
                        min_distance = current_distance
                        min_route = current_route
                        min_node = node

            if min_route is not None:
                assigned_nodes_for_workers[worker_idx] |= {min_node}

    return assigned_nodes_for_workers

# Plot the routes of a worker on a map and save as a html 
def plot_routes_on_map(workers, jobs, assigned_nodes_for_workers, gmaps):
    for worker_idx, worker in workers.iterrows():
        assigned_nodes = list(assigned_nodes_for_workers[worker_idx])

        # Choose an address as the center of the map
        center_address = jobs["address"].iloc[assigned_nodes[0]]
        center_location = gmaps.geocode(center_address)[0]["geometry"]["location"]
        center_lat, center_lng = center_location["lat"], center_location["lng"]

        # Display the assignments on a map for each worker
        gmap = gmplot.GoogleMapPlotter(center_lat, center_lng, zoom=12)

        # Set a unique color for each worker
        colors = ["red", "blue", "green", "purple", "orange", "yellow", "black", "gray"]
        color_index = worker_idx % len(colors)
        color = colors[color_index]

        lats = [gmaps.geocode(jobs["address"].iloc[job])[0]["geometry"]["location"]["lat"] for job in assigned_nodes]
        lngs = [gmaps.geocode(jobs["address"].iloc[job])[0]["geometry"]["location"]["lng"] for job in assigned_nodes]

        # Plot the route for the worker
        if len(assigned_nodes) > 1:
            gmap.plot(lats, lngs, color=color, edge_width=2.5)
        else:
            gmap.marker(lats[0], lngs[0], color=color)

        # Name the file after the worker and the current date
        today = datetime.date.today().strftime("%Y-%m-%d")
        filename = f"routes/{worker['worker_name']}_{today}.html"
        gmap.draw(filename)


# 1. Reads input files
# 2. Calculates the distance matrix 
# 3. Finds the optimal routes 
# 4. Prints these routes 
# 5. Visualises them on a map 
def main():
    # Declare your Google maps API 
    #gmaps = googlemaps.Client(key='')

    # Get the CSV file names 
    worker_file = input("Enter the name of the worker csv file: ")
    job_file = input("Enter the name of the job csv file: ")
    workers, jobs = read_csv_files(worker_file, job_file)
    
    # Declare the min/max job IDs to figure out the distance matrix file 
    min_job_id = jobs["job_ID"].min()
    max_job_id = jobs["job_ID"].max()
    distance_matrix_file = f"distance_IDs_{min_job_id}_to_{max_job_id}.pkl"
    
    # Get the distance matrix to use with the TSP 
    distance_matrix = calculate_distance_matrix(jobs, distance_matrix_file)
    
    # Assign jobs to each worker. This invokes the route manager to solve the TSP 
    # given the distance matrix and workers
    assigned_nodes_for_workers = assign_jobs_to_workers(workers, distance_matrix)
    
    # Print the solution
    for worker_idx, worker in workers.iterrows():
        assigned_nodes = list(assigned_nodes_for_workers[worker_idx])
        print_solution(worker, assigned_nodes, distance_matrix, jobs)
        
    # Only enable if gmaps API key is set  
    # Plots the routes for each worker on a map, and stores it as a html file 
    #plot_routes_on_map(workers, jobs, assigned_nodes_for_workers, gmaps):
    
    
# Main entry point 
if __name__ == "__main__":
    main()
    