import numpy as np
import matplotlib.pyplot as plt
import math
import random
import pandas as pd
import requests
import json



# --- 1. DATA GENERATION (MOCKING THE GRAPH) ---
MAX_GAP = 3  # Maximum number of small cities allowed between large cities

def load_slovak_cities(file_path):
    # 1. Load the file using the semicolon delimiter
    df = pd.read_csv(file_path, delimiter=';')

    # 2. Data Cleaning
    # The file has many empty rows at the end; remove them.
    df = df.dropna(subset=['Name'])
    
    # 3. Coordinate Correction
    # Your file has coordinates like 481.439 which implies they are multiplied by 10.
    # We divide by 10 to get standard GPS coordinates (e.g., 48.1439).
    df['Lat'] = df['Lat'] / 10.0
    df['Lon'] = df['Lon'] / 10.0
    
    # 4. Convert Population to Integer (it reads as float by default)
    df['Pop'] = df['Pop'].astype(int)

    # 5. Extract cities into a list of dictionaries
    cities_list = []
    
    # iterrows() allows us to process each city individually
    for index, row in df.iterrows():
        city_info = {
            "name": row['Name'],
            "lat": row['Lat'],
            "lon": row['Lon'],
            "population": row['Pop']
        }
        cities_list.append(city_info)
        
    return cities_list
file_name = 'slovakia_cities.csv'
all_cities = load_slovak_cities(file_name)


# --- 2. DISTANCE MATRIX (The Graph Edges) ---
def get_driving_distance(lat1, lon1, lat2, lon2):
    """
    Calculates driving distance (in km) between two points using OSRM public API.
    """
    # OSRM expects coordinates as 'longitude,latitude'
    coordinates = f"{lon1},{lat1};{lon2},{lat2}"
    
    # We use the 'route' service for simple A to B
    url = f"http://router.project-osrm.org/route/v1/driving/{coordinates}?overview=false"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if data["code"] == "Ok":
            # Distance is returned in meters, convert to km
            distance_meters = data["routes"][0]["distance"]
            return distance_meters / 1000.0
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def create_distance_matrix(cities):
    """
    Creates a distance matrix by calling get_driving_distance for all city pairs.
    Stores the matrix as a numpy file for later use.
    Returns a 2D numpy array where dist_matrix[i][j] is the distance from city i to city j.
    """

    n = 3#TODO ALDATU ALDATU ALDATU
    dist_matrix = np.zeros((n, n)) 
    
    for i in range(n):
        for j in range((n + i) % n):
            if i == j:
                dist_matrix[i][j] = 0
            else:
                distance = get_driving_distance(
                    cities[i]["lat"], 
                    cities[i]["lon"],
                    cities[j]["lat"], 
                    cities[j]["lon"]
                )
                dist_matrix[i][j] = distance if distance is not None else float('inf')
                dist_matrix[j][i] = distance if distance is not None else float('inf')
                print(f"Distance {cities[i]['name']} -> {cities[j]['name']}: {distance} km")
    
    # Save the distance matrix to a file
    np.save('distance_matrix.npy', dist_matrix)
    print("Distance matrix saved to 'distance_matrix.npy'")
    
    return dist_matrix

dist_matrix = create_distance_matrix(all_cities)
cities = all_cities
print(dist_matrix)
# --- 3. THE COST FUNCTION WITH CONSTRAINTS ---
def calculate_total_cost(tour, dist_matrix, cities):
    """
    Returns: Total Distance + Penalty for violating spacing constraint.
    """
    total_dist = 0
    small_city_streak = 0
    penalty = 0
    
    penalty_weight = 1000 # High cost to discourage constraint violation

    for i in range(len(tour)):
        from_city = tour[i]
        to_city = tour[(i + 1) % len(tour)] # Wrap around to start
        
        total_dist += dist_matrix[from_city][to_city]
        
        # Check constraint logic
        if cities[from_city]["is_large"]:
            small_city_streak = 0
        else:
            small_city_streak += 1
            
        if small_city_streak > MAX_GAP:
            penalty += penalty_weight * (small_city_streak - MAX_GAP)

    return total_dist + penalty, total_dist

# --- 4. SIMULATED ANNEALING SOLVER ---
def simulated_annealing(cities, dist_matrix):
    n = len(cities)
    # Initial Solution: Random shuffle (keeping Bratislava at index 0)
    current_tour = list(range(n))
    current_tour.pop(0) # Remove Start (Bratislava)
    random.shuffle(current_tour)
    current_tour = [0] + current_tour # Add Start back
    
    current_energy, current_dist = calculate_total_cost(current_tour, dist_matrix, cities)
    
    best_tour = list(current_tour)
    best_energy = current_energy
    best_dist = current_dist
    
    # SA Parameters
    temp = 10000
    cooling_rate = 0.9995
    absolute_zero = 0.1
    
    iteration = 0
    
    print("Starting Simulated Annealing...")
    
    while temp > absolute_zero:
        # Create neighbor: Swap two random cities (excluding start)
        new_tour = list(current_tour)
        i, j = random.sample(range(1, n), 2)
        new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
        
        new_energy, new_dist = calculate_total_cost(new_tour, dist_matrix, cities)
        
        # Acceptance Probability
        delta = new_energy - current_energy
        if delta < 0 or random.random() < math.exp(-delta / temp):
            current_tour = new_tour
            current_energy = new_energy
            current_dist = new_dist
            
            if current_energy < best_energy:
                best_tour = list(current_tour)
                best_energy = current_energy
                best_dist = current_dist
        
        temp *= cooling_rate
        iteration += 1
        
        if iteration % 10000 == 0:
            print(f"Iter {iteration}: Temp={temp:.2f}, Best Dist={best_dist:.2f}")

    return best_tour, best_dist

# --- EXECUTION ---
best_route, min_distance = simulated_annealing(cities, dist_matrix)

# --- 5. VERIFICATION & OUTPUT ---
def verify_and_plot(tour, cities):
    generate_slovakia_data()
    # Verification of spacing
    max_streak = 0
    current_streak = 0
    valid = True
    
    for idx in tour:
        if cities[idx]["is_large"]:
            current_streak = 0
        else:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
    
    print("-" * 40)
    print(f"FINAL RESULT:")
    print(f"Total Distance: {min_distance:.2f}")
    print(f"Max gap between large cities: {max_streak} cities")
    if max_streak <= MAX_GAP:
        print("Constraint Status: SATISFIED (Routes are evenly spaced)")
    else:
        print("Constraint Status: FAILED (Adjust penalty weight)")

    # Plotting
    x_coords = [cities[i]["coords"][0] for i in tour] + [cities[tour[0]]["coords"][0]]
    y_coords = [cities[i]["coords"][1] for i in tour] + [cities[tour[0]]["coords"][1]]
    
    plt.figure(figsize=(10, 8))
    plt.plot(x_coords, y_coords, 'b-', alpha=0.6, label='Route')
    
    # Plot Small Cities
    sx = [c["coords"][0] for c in cities if not c["is_large"]]
    sy = [c["coords"][1] for c in cities if not c["is_large"]]
    plt.scatter(sx, sy, c='gray', s=20, label='Small City')
    
    # Plot Large Cities
    lx = [c["coords"][0] for c in cities if c["is_large"]]
    ly = [c["coords"][1] for c in cities if c["is_large"]]
    plt.scatter(lx, ly, c='red', s=100, zorder=5, label='Large City (>50k)')
    
    # Mark Start
    start = cities[tour[0]]["coords"]
    plt.scatter(start[0], start[1], c='green', marker='*', s=200, zorder=10, label='Bratislava (Start)')
    
    plt.title(f"Optimal TSP Route (Slovakia Model)\nDist: {min_distance:.2f} | Max Gap: {max_streak}")
    plt.legend()
    plt.show()

verify_and_plot(best_route, cities)