import pandas as pd

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

# --- Usage ---
file_name = 'slovakia_cities.csv'
try:
    all_cities = load_slovak_cities(file_name)
    
    # Print the total count
    print(f"Successfully loaded {len(all_cities)} cities.")
    
    # Print the first city to verify
    print("First city:", all_cities[0])
    
    # Example: Print only large cities (>50k)
    print("\nLarge Cities:")
    for city in all_cities:
        if city['population'] > 50000:
            print(f"- {city['name']} (Pop: {city['population']})")
            
except FileNotFoundError:
    print("Please make sure 'slovakia_cities.csv' is in the same folder.")