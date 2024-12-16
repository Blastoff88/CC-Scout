import csv
import requests
import tkinter as tk
from tkinter import ttk, messagebox
import hashlib
import re

BEST_AUTO_SAMPLES_COLOR = "#FFDDC1"  # Example color (light red)
BEST_AUTO_SPECIMENS_COLOR = "#C1E1FF"  # Example color (light blue)
BEST_TELEOP_SAMPLES_COLOR = "#C1FFC1"  # Example color (light green)
BEST_TELEOP_SPECIMENS_COLOR = "#FFD1C1"  # Example color (light pink)

last_file_hash = None  # Initialize the last file hash

def get_team_name(team_number):
    url = "https://api.ftcscout.org/graphql"
    query = f"""
    {{
      teamByNumber(number: {team_number}) {{
        name
      }}
    }}
    """
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "query": query
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            team_name = data.get('data', {}).get('teamByNumber', {}).get('name', 'No team found')
            return team_name
        else:
            return "Unknown"
    except Exception as e:
        return "Unknown"

def parse_teleop_input(value):
    """Parse teleOp input and return the numerical value."""
    if value == "Too much":
        return 18
    match = re.match(r'(\d+)(?:-(\d+))?', value)
    if match:
        return int(match.group(1))  # Return the lower bound
    return 0  # Default if no match

def parse_ascent_level(value):
    """Convert ascent level to a numerical value."""
    ascent_levels = {
        "Nothing": 0,
        "Park": 1,
        "Ascent 1": 1,
        "Ascent 2": 2,
        "Ascent 3": 3
    }
    return ascent_levels.get(value, 0)

def organize_matches_by_team(csv_file):
    team_data = {}
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        next(reader, None)
        for row in reader:
            match_number = row[5]
            team_number = int(row[6])
            auto_park = 1 if row[7] == 'Yes' else 0
            auto_samples = parse_teleop_input(row[8])
            auto_specimens = parse_teleop_input(row[9])
            teleop_samples = parse_teleop_input(row[10])
            teleop_specimens = parse_teleop_input(row[11])
            ascent_level = parse_ascent_level(row[12])

            if match_number not in team_data:
                team_data[match_number] = {
                    'teams': {},
                    'auto_park': [],
                    'auto_samples': [],
                    'auto_specimens': [],
                    'teleop_samples': [],
                    'teleop_specimens': [],
                    'ascent_levels': []
                }

            if team_number not in team_data[match_number]['teams']:
                team_data[match_number]['teams'][team_number] = get_team_name(team_number)

            team_data[match_number]['auto_park'].append(auto_park)
            team_data[match_number]['auto_samples'].append(auto_samples)
            team_data[match_number]['auto_specimens'].append(auto_specimens)
            team_data[match_number]['teleop_samples'].append(teleop_samples)
            team_data[match_number]['teleop_specimens'].append(teleop_specimens)
            team_data[match_number]['ascent_levels'].append(ascent_level)

    return team_data

def calculate_hash(file_path):
    """Calculate the SHA256 hash of the CSV file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            hash_sha256.update(byte_block)
    return hash_sha256.hexdigest()

def display_data():
    global last_file_hash, root

    current_file_hash = calculate_hash(csv_file_path)
    
    if current_file_hash == last_file_hash:
        messagebox.showinfo("Info", "Data is already up-to-date.")
        return

    for item in tree.get_children():
        tree.delete(item)

    team_data = organize_matches_by_team(csv_file_path)

    # Create a new structure to hold aggregated data by team
    aggregated_data = {}

    for match_number, data in team_data.items():
        for team_number, team_name in data['teams'].items():
            if team_number not in aggregated_data:
                aggregated_data[team_number] = {
                    'team_name': team_name,
                    'match_numbers': [],
                    'auto_park': [],
                    'auto_samples': [],
                    'auto_specimens': [],
                    'teleop_samples': [],
                    'teleop_specimens': [],
                    'ascent_levels': []
                }
            
            # Find the index of the team in the match data
            team_index = list(data['teams'].keys()).index(team_number)

            # Append match number and scores to the aggregated data
            aggregated_data[team_number]['match_numbers'].append(match_number)
            aggregated_data[team_number]['auto_park'].append(data['auto_park'][team_index])
            aggregated_data[team_number]['auto_samples'].append(data['auto_samples'][team_index])
            aggregated_data[team_number]['auto_specimens'].append(data['auto_specimens'][team_index])
            aggregated_data[team_number]['teleop_samples'].append(data['teleop_samples'][team_index])
            aggregated_data[team_number]['teleop_specimens'].append(data['teleop_specimens'][team_index])
            aggregated_data[team_number]['ascent_levels'].append(data['ascent_levels'][team_index])

    # Now calculate averages and insert into the treeview
    best_auto_samples_team = None
    best_auto_samples_value = float('-inf')
    best_auto_specimens_team = None
    best_auto_specimens_value = float('-inf')
    best_teleop_samples_team = None
    best_teleop_samples_value = float('-inf')
    best_teleop_specimens_team = None
    best_teleop_specimens_value = float('-inf')

    for team_number, data in aggregated_data.items():
        avg_auto_samples = sum(data['auto_samples']) / len(data['auto_samples']) if data['auto_samples'] else 0
        avg_auto_specimens = sum(data['auto_specimens']) / len(data['auto_specimens']) if data['auto_specimens'] else 0
        avg_teleop_samples = sum(data['teleop_samples']) / len(data['teleop_samples']) if data['teleop_samples'] else 0
        avg_teleop_specimens = sum(data['teleop_specimens']) / len(data['teleop_specimens']) if data['teleop_specimens'] else 0

        # Determine the best teams
        if avg_auto_samples > best_auto_samples_value:
            best_auto_samples_value = avg_auto_samples
            best_auto_samples_team = team_number

        if avg_auto_specimens > best_auto_specimens_value:
            best_auto_specimens_value = avg_auto_specimens
            best_auto_specimens_team = team_number

        if avg_teleop_samples > best_teleop_samples_value:
            best_teleop_samples_value = avg_teleop_samples
            best_teleop_samples_team = team_number

        if avg_teleop_specimens > best_teleop_specimens_value:
            best_teleop_specimens_value = avg_teleop_specimens
            best_teleop_specimens_team = team_number

    # Insert the aggregated averages into the treeview and highlight the best teams
    for team_number, data in aggregated_data.items():
        match_numbers = ', '.join(data['match_numbers'])  # Join match numbers for display
        avg_auto_park = sum(data['auto_park']) / len(data['auto_park']) if data['auto_park'] else 0
        avg_auto_samples = sum(data['auto_samples']) / len(data['auto_samples']) if data['auto_samples'] else 0
        avg_auto_specimens = sum(data['auto_specimens']) / len(data['auto_specimens']) if data['auto_specimens'] else 0
        avg_teleop_samples = sum(data['teleop_samples']) / len(data['teleop_samples']) if data['teleop_samples'] else 0
        avg_teleop_specimens = sum(data['teleop_specimens']) / len(data['teleop_specimens']) if data['teleop_specimens'] else 0
        avg_ascent_level = sum(data['ascent_levels']) / len(data['ascent_levels']) if data['ascent_levels'] else 0

        # Insert the aggregated averages into the treeview
        item_id = tree.insert("", "end", values=(
            team_number,  # Team Number
            data['team_name'],  # Team Name
            match_numbers,  # Match Numbers
            avg_auto_park,
            avg_auto_samples,
            avg_auto_specimens,
            avg_teleop_samples,
            avg_teleop_specimens,
            avg_ascent_level
        ))

        # Highlight the best teams based on the override variable
        if team_number == best_auto_samples_team:
            tree.item(item_id, tags=('best_auto_samples',))
        if team_number == best_auto_specimens_team:
            tree.item(item_id, tags=('best_auto_specimens',))
        if team_number == best_teleop_samples_team:
            tree.item(item_id, tags=('best_teleop_samples',))
        if team_number == best_teleop_specimens_team:
            tree.item(item_id, tags=('best_teleop_specimens',))

    # Apply the color tags to the Treeview
    tree.tag_configure('best_auto_samples', background=BEST_AUTO_SAMPLES_COLOR)
    tree.tag_configure('best_auto_specimens', background=BEST_AUTO_SPECIMENS_COLOR)
    tree.tag_configure('best_teleop_samples', background=BEST_TELEOP_SAMPLES_COLOR)
    tree.tag_configure('best_teleop_specimens', background=BEST_TELEOP_SPECIMENS_COLOR)

    # Create a key at the bottom of the GUI
    key_frame = tk.Frame(root)
    key_frame.pack(side='bottom', fill='x')

    tk.Label(key_frame, text="Key:").pack(side='left')
    tk.Label(key_frame, text="Best Auto Samples", bg=BEST_AUTO_SAMPLES_COLOR).pack(side='left', padx=5)
    tk.Label(key_frame, text="Best Auto Specimens", bg=BEST_AUTO_SPECIMENS_COLOR).pack(side='left', padx=5)
    tk.Label(key_frame, text="Best Teleop Samples", bg=BEST_TELEOP_SAMPLES_COLOR).pack(side='left', padx=5)
    tk.Label(key_frame, text="Best Teleop Specimens", bg=BEST_TELEOP_SPECIMENS_COLOR).pack(side='left', padx=5)

    last_file_hash = current_file_hash

def initialize_gui():
    """Set up the main GUI components."""
    global tree, root
    root = tk.Tk()
    root.title("Team Data Viewer")

    # Create a frame for the Treeview and scrollbar
    frame = tk.Frame(root)
    frame.pack(expand=True, fill='both')

    # Set up the treeview
    tree = ttk.Treeview(frame, columns=("Team Number", "Team Name", "Match Numbers", "Avg Auto Park", "Avg Auto Samples", "Avg Auto Specimens", "Avg Teleop Samples", "Avg Teleop Specimens", "Avg Ascent Level"), show='headings')

    # Define column widths
    tree.column("Team Number", width=100)
    tree.column("Team Name", width=150)
    tree.column("Match Numbers", width=200)
    tree.column("Avg Auto Park", width=100)
    tree.column("Avg Auto Samples", width=100)
    tree.column("Avg Auto Specimens", width=100)
    tree.column("Avg Teleop Samples", width=100)
    tree.column("Avg Teleop Specimens", width=100)
    tree.column("Avg Ascent Level", width=100)

    for col in tree["columns"]:
        tree.heading(col, text=col)

    # Create a vertical scrollbar
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    vsb.pack(side='right', fill='y')
    tree.configure(yscrollcommand=vsb.set)

    # Create a horizontal scrollbar
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    hsb.pack(side='bottom', fill='x')
    tree.configure(xscrollcommand=hsb.set)

    tree.pack(expand=True, fill='both')

    # Add a button to refresh data
    refresh_button = tk.Button(root, text="Refresh Data", command=display_data)
    refresh_button.pack()

    # Start the GUI event loop
    root.mainloop()

# Define the CSV file path
csv_file_path = "scoutingForm.csv"

# Initialize the GUI
initialize_gui()
