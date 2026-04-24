import json
from copy import deepcopy

# Real weights from the actual data file (82 entries)
real_weights = [
    259.7, 260.3, 260.2, 260.9, 261.8, 259.6, 259.2, 258.9, 258.4, 257.9,
    257.5, 257.3, 256.7, 257.9, 258.5, 258.1, 258.1, 260.2, 258,   257.8,
    258.8, 259.6, 258.2, 256,   256.5, 257,   256,   257.9, 259.9, 258.7,
    257.6, 259.6, 257.2, 256.4, 257.4, 257.9, 257.4, 257,   255.8, 255.8,
    256.9, 257.2, 256.1, 257.8, 255.6, 255.9, 258,   256.8, 257,   260.3,
    257.1, 256.1, 257.9, 259.2, 256.6, 255.9, 256.2, 256.9, 257.4, 256.7,
    255.2, 255.2, 257.1, 258.5, 259.3, 256.1, 255.9, 256.2, 258.8, 259.1,
    261.1, 257.4, 257.3, 257.1, 257.3, 258.2, 258.5, 256.5, 254.2, 254.1,
    253.7, 254.8,
]

# Compute daily deltas from real data
deltas = [round(real_weights[i] - real_weights[i-1], 1) for i in range(1, len(real_weights))]

# Build fictional weights starting at 200.0
fictional_start = 200.0
fictional_weights = [fictional_start]
for d in deltas:
    fictional_weights.append(round(fictional_weights[-1] + d, 1))

# Food name mapping: real -> fictional
food_map = {
    "breakfast":         "oatmeal bowl",
    "salmon sandwiches": "turkey wraps",
    "veggies":           "garden salad",
    "fairlife":          "protein shake",
    "fairlight":         "protein shake",
    "banana":            "apple",
    "bb cafe":           "corner diner",
    "coke":              "soda",
    "popcorn":           "popcorn",
    "hot dog":           "bratwurst",
    "rouses pack":       "snack bag",
    "bluebell":          "ice cream",
    "chips":             "tortilla chips",
    "caramel cashews":   "honey roasted peanuts",
    "twix bar":          "candy bar",
    "seafood cornbread": "fish tacos",
    "burger":            "cheeseburger",
    "chicken bites":     "chicken tenders",
    "piccadilly":        "diner special",
    "pie":               "pie slice",
    "chicken sandwiches":"grilled chicken sandwich",
    "chai latte":        "green tea latte",
    "bread":             "sourdough bread",
    "crab cakes":        "shrimp cakes",
    "seafood pasta":     "pasta primavera",
    "shake shack":       "five guys",
    "reeses":            "peanut butter cups",
    "reeses cup":        "peanut butter cup",
    "yogurt pretzels":   "chocolate pretzels",
    "tuna":              "tuna salad",
    "borden":            "chocolate milk",
    "cake":              "birthday cake",
    "stuffed crabs":     "stuffed peppers",
    "boiled potatoes":   "roasted potatoes",
    "sour cream":        "sour cream",
    "egg mcmuffins":     "breakfast sandwiches",
    "hash browns":       "home fries",
    "caniac combo":      "fried chicken combo",
    "caniac":            "fried chicken",
    "canes":             "fried chicken strips",
    "spaghetti":         "pasta marinara",
    "sphagetti":         "pasta marinara",
    "rum and cokes":     "cocktails",
    "nestle bites":      "chocolate bites",
    "taquito":           "breakfast burrito",
    "sliders":           "mini burgers",
    "fries":             "sweet potato fries",
    "hot tamales":       "red hots",
    "lean cuisine":      "frozen entree",
    "caramel cookie":    "oatmeal cookie",
    "drinks":            "sodas",
    "tuna sandwiches":   "tuna wraps",
}

# Notes mapping
note_map = {
    "waist 48":                                   "waist 36",
    "burger and chicken bites from Shake Shack":  "cheeseburger and chicken tenders from Five Guys",
    "1 banana and 1 fairlife were late at night": "1 apple and 1 protein shake were late at night",
}

# Real entry data (dates, foods, notes) — we'll re-map foods and notes
real_entries = [
    {"date": "2026-02-01", "foods": [], "notes": ""},
    {"date": "2026-02-02", "foods": [], "notes": ""},
    {"date": "2026-02-03", "foods": [], "notes": ""},
    {"date": "2026-02-04", "foods": [], "notes": ""},
    {"date": "2026-02-05", "foods": [], "notes": ""},
    {"date": "2026-02-06", "foods": [], "notes": ""},
    {"date": "2026-02-07", "foods": [], "notes": ""},
    {"date": "2026-02-08", "foods": [], "notes": ""},
    {"date": "2026-02-09", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"veggies","qty":1},{"name":"fairlife","qty":2}], "notes": "waist 48"},
    {"date": "2026-02-10", "foods": [{"name":"breakfast","qty":1},{"name":"coke","qty":1},{"name":"popcorn","qty":1},{"name":"hot dog","qty":1},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":3},{"name":"banana","qty":1}], "notes": ""},
    {"date": "2026-02-11", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"veggies","qty":1},{"name":"fairlife","qty":3},{"name":"banana","qty":1}], "notes": ""},
    {"date": "2026-02-12", "foods": [{"name":"breakfast","qty":1},{"name":"banana","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-02-13", "foods": [{"name":"breakfast","qty":1},{"name":"banana","qty":1},{"name":"twix bar","qty":1},{"name":"rouses pack","qty":1},{"name":"seafood cornbread","qty":1},{"name":"fairlife","qty":2},{"name":"rouses pack","qty":1}], "notes": ""},
    {"date": "2026-02-14", "foods": [{"name":"breakfast","qty":1},{"name":"burger","qty":1},{"name":"chicken bites","qty":1},{"name":"fairlife","qty":2},{"name":"rouses pack","qty":1}], "notes": "burger and chicken bites from Shake Shack"},
    {"date": "2026-02-15", "foods": [{"name":"breakfast","qty":1},{"name":"banana","qty":2},{"name":"piccadilly","qty":1},{"name":"pie","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-02-16", "foods": [{"name":"breakfast","qty":1},{"name":"chicken sandwiches","qty":2},{"name":"fairlife","qty":3},{"name":"banana","qty":1}], "notes": ""},
    {"date": "2026-02-17", "foods": [{"name":"breakfast","qty":1},{"name":"chai latte","qty":1},{"name":"coke","qty":1},{"name":"popcorn","qty":1},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":2},{"name":"caramel cashews","qty":1},{"name":"bluebell","qty":1},{"name":"chips","qty":1}], "notes": ""},
    {"date": "2026-02-18", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-02-19", "foods": [{"name":"breakfast","qty":1},{"name":"banana","qty":2},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":3}], "notes": "1 banana and 1 fairlife were late at night"},
    {"date": "2026-02-20", "foods": [], "notes": ""},
    {"date": "2026-02-21", "foods": [], "notes": ""},
    {"date": "2026-02-22", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-02-23", "foods": [{"name":"breakfast","qty":1},{"name":"banana","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-02-24", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":3},{"name":"bread","qty":1}], "notes": ""},
    {"date": "2026-02-25", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"veggies","qty":1},{"name":"bluebell","qty":1},{"name":"caramel cashews","qty":1},{"name":"chips","qty":1}], "notes": ""},
    {"date": "2026-02-26", "foods": [{"name":"breakfast","qty":1},{"name":"taquito","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-02-27", "foods": [{"name":"breakfast","qty":1},{"name":"rouses pack","qty":2},{"name":"crab cakes","qty":2},{"name":"chips","qty":1},{"name":"bluebell","qty":1}], "notes": ""},
    {"date": "2026-02-28", "foods": [{"name":"breakfast","qty":1},{"name":"caniac combo","qty":1},{"name":"fairlife","qty":3},{"name":"bread","qty":2}], "notes": ""},
    {"date": "2026-03-01", "foods": [{"name":"breakfast","qty":1},{"name":"bread","qty":2},{"name":"caniac combo","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-03-02", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"fairlife","qty":2},{"name":"reeses","qty":1},{"name":"chips","qty":1},{"name":"bluebell","qty":1}], "notes": ""},
    {"date": "2026-03-03", "foods": [{"name":"breakfast","qty":1},{"name":"twix bar","qty":1},{"name":"hot dog","qty":1},{"name":"rouses pack","qty":1},{"name":"bluebell","qty":1}], "notes": ""},
    {"date": "2026-03-04", "foods": [{"name":"breakfast","qty":1},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-05", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-03-06", "foods": [{"name":"breakfast","qty":1},{"name":"nestle bites","qty":1},{"name":"hot dog","qty":1},{"name":"crab cakes","qty":2},{"name":"seafood pasta","qty":1},{"name":"fairlife","qty":2},{"name":"rouses pack","qty":1}], "notes": ""},
    {"date": "2026-03-07", "foods": [{"name":"breakfast","qty":1},{"name":"shake shack","qty":1},{"name":"fairlife","qty":3},{"name":"bread","qty":2}], "notes": ""},
    {"date": "2026-03-08", "foods": [{"name":"breakfast","qty":1},{"name":"chips","qty":1},{"name":"reeses cup","qty":1},{"name":"yogurt pretzels","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-09", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"tuna","qty":1},{"name":"coke","qty":1}], "notes": ""},
    {"date": "2026-03-10", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"bluebell","qty":2}], "notes": ""},
    {"date": "2026-03-11", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"veggies","qty":1},{"name":"borden","qty":3}], "notes": ""},
    {"date": "2026-03-12", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"cake","qty":1},{"name":"caramel cashews","qty":1},{"name":"bluebell","qty":1}], "notes": ""},
    {"date": "2026-03-13", "foods": [{"name":"breakfast","qty":1},{"name":"rouses pack","qty":1},{"name":"stuffed crabs","qty":2},{"name":"fairlife","qty":2},{"name":"boiled potatoes","qty":3},{"name":"sour cream","qty":1}], "notes": ""},
    {"date": "2026-03-14", "foods": [{"name":"egg mcmuffins","qty":2},{"name":"hash browns","qty":1},{"name":"boiled potatoes","qty":4},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-03-15", "foods": [{"name":"breakfast","qty":1},{"name":"burger","qty":1},{"name":"chicken bites","qty":1},{"name":"fairlife","qty":4}], "notes": "burger and chicken bites from Shake Shack"},
    {"date": "2026-03-16", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"veggies","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-17", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-18", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"caramel cashews","qty":1},{"name":"chips","qty":1},{"name":"bluebell","qty":1}], "notes": ""},
    {"date": "2026-03-19", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"rum and cokes","qty":5}], "notes": ""},
    {"date": "2026-03-20", "foods": [{"name":"breakfast","qty":1},{"name":"nestle bites","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-21", "foods": [{"name":"breakfast","qty":1},{"name":"canes","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-22", "foods": [{"name":"breakfast","qty":1},{"name":"spaghetti","qty":1},{"name":"canes","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-23", "foods": [], "notes": ""},
    {"date": "2026-03-24", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":3},{"name":"yogurt pretzels","qty":1},{"name":"hot tamales","qty":1}], "notes": ""},
    {"date": "2026-03-25", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlight","qty":3},{"name":"bluebell","qty":1},{"name":"chips","qty":1},{"name":"cookies","qty":6}], "notes": ""},
    {"date": "2026-03-26", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-03-27", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":2},{"name":"rum and cokes","qty":7}], "notes": ""},
    {"date": "2026-03-28", "foods": [{"name":"breakfast","qty":1},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":2},{"name":"tuna","qty":1},{"name":"coke","qty":1}], "notes": ""},
    {"date": "2026-03-29", "foods": [{"name":"breakfast","qty":1},{"name":"bread","qty":2},{"name":"sliders","qty":3},{"name":"fries","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-03-30", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"chips","qty":1},{"name":"bluebell","qty":1},{"name":"caramel cashews","qty":1}], "notes": ""},
    {"date": "2026-03-31", "foods": [{"name":"breakfast","qty":1},{"name":"popcorn","qty":1},{"name":"coke","qty":1},{"name":"nestle bites","qty":1},{"name":"bb cafe","qty":1}], "notes": ""},
    {"date": "2026-04-01", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-04-02", "foods": [{"name":"breakfast","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"fairlife","qty":3},{"name":"rum and cokes","qty":2}], "notes": ""},
    {"date": "2026-04-03", "foods": [], "notes": ""},
    {"date": "2026-04-04", "foods": [{"name":"caniac","qty":1},{"name":"chips","qty":1},{"name":"bluebell","qty":1}], "notes": ""},
    {"date": "2026-04-05", "foods": [{"name":"breakfast","qty":1},{"name":"shake shack","qty":1},{"name":"fries","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-04-06", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"sphagetti","qty":1}], "notes": ""},
    {"date": "2026-04-07", "foods": [{"name":"breakfast","qty":1},{"name":"caramel cookie","qty":1},{"name":"nestle bites","qty":1},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":3},{"name":"sphagetti","qty":1}], "notes": ""},
    {"date": "2026-04-08", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"drinks","qty":4}], "notes": ""},
    {"date": "2026-04-09", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"rouses pack","qty":1},{"name":"bluebell","qty":1},{"name":"chips","qty":1}], "notes": ""},
    {"date": "2026-04-10", "foods": [{"name":"breakfast","qty":1},{"name":"caramel cashews","qty":1},{"name":"hot dog","qty":1},{"name":"rouses pack","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-04-11", "foods": [{"name":"breakfast","qty":1},{"name":"caniac","qty":1},{"name":"fairlife","qty":4},{"name":"chips","qty":1}], "notes": ""},
    {"date": "2026-04-12", "foods": [{"name":"breakfast","qty":1},{"name":"piccadilly","qty":1},{"name":"pie","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-04-13", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"tuna","qty":1},{"name":"coke","qty":1}], "notes": ""},
    {"date": "2026-04-14", "foods": [{"name":"breakfast","qty":1},{"name":"tuna","qty":1},{"name":"salmon sandwiches","qty":2},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-04-15", "foods": [], "notes": ""},
    {"date": "2026-04-16", "foods": [{"name":"breakfast","qty":1},{"name":"rouses pack","qty":1},{"name":"bluebell","qty":1},{"name":"spaghetti","qty":1},{"name":"lean cuisine","qty":1}], "notes": ""},
    {"date": "2026-04-17", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"fairlife","qty":2},{"name":"yogurt pretzels","qty":1},{"name":"chips","qty":1},{"name":"bluebell","qty":1}], "notes": ""},
    {"date": "2026-04-18", "foods": [{"name":"breakfast","qty":1},{"name":"shake shack","qty":1},{"name":"fairlife","qty":2},{"name":"rouses pack","qty":1}], "notes": ""},
    {"date": "2026-04-19", "foods": [{"name":"breakfast","qty":1},{"name":"piccadilly","qty":1},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-04-20", "foods": [{"name":"breakfast","qty":1},{"name":"tuna sandwiches","qty":2},{"name":"fairlife","qty":3}], "notes": ""},
    {"date": "2026-04-21", "foods": [{"name":"breakfast","qty":1},{"name":"bb cafe","qty":1},{"name":"pie","qty":1},{"name":"drinks","qty":5}], "notes": ""},
    {"date": "2026-04-22", "foods": [{"name":"breakfast","qty":1},{"name":"piccadilly","qty":1},{"name":"pie","qty":1},{"name":"chips","qty":1},{"name":"fairlife","qty":2}], "notes": ""},
    {"date": "2026-04-23", "foods": [], "notes": ""},
]

def map_foods(foods):
    return [{"name": food_map.get(f["name"], f["name"]), "qty": f["qty"]} for f in foods]

def map_note(note):
    return note_map.get(note, note)

# Build fictional entries
entries = []
for i, real in enumerate(real_entries):
    entries.append({
        "date": real["date"],
        "weight": fictional_weights[i],
        "foods": map_foods(real["foods"]),
        "notes": map_note(real["notes"]),
    })

# Scale factor for historical weights
scale = 200.0 / 259.7

def scale_weight(w):
    return round(w * scale, 1)

doctor_visits = [
    {"date": "2017-03-21", "doctor": "Martinez", "officeWeight": scale_weight(292.4), "homeWeight": scale_weight(287),   "notes": ""},
    {"date": "2021-03-23", "doctor": "Martinez", "officeWeight": scale_weight(256),   "homeWeight": scale_weight(253.6), "notes": ""},
    {"date": "2021-05-24", "doctor": "Patel",    "officeWeight": scale_weight(250.8), "homeWeight": scale_weight(246.2), "notes": ""},
    {"date": "2022-05-06", "doctor": "Patel",    "officeWeight": scale_weight(246),   "homeWeight": scale_weight(241.4), "notes": ""},
    {"date": "2022-07-13", "doctor": "Patel",    "officeWeight": scale_weight(247.4), "homeWeight": scale_weight(240.8), "notes": ""},
    {"date": "2022-12-29", "doctor": "Patel",    "officeWeight": scale_weight(250.4), "homeWeight": scale_weight(245),   "notes": ""},
    {"date": "2023-11-08", "doctor": "Patel",    "officeWeight": scale_weight(260.6), "homeWeight": scale_weight(256.8), "notes": ""},
    {"date": "2023-12-13", "doctor": "Martinez", "officeWeight": scale_weight(265.2), "homeWeight": scale_weight(260.6), "notes": ""},
    {"date": "2024-01-17", "doctor": "Martinez", "officeWeight": scale_weight(270),   "homeWeight": scale_weight(261.6), "notes": ""},
    {"date": "2025-05-22", "doctor": "Patel",    "officeWeight": scale_weight(260.9), "homeWeight": scale_weight(258.2), "notes": ""},
    {"date": "2025-09-25", "doctor": "Martinez", "officeWeight": scale_weight(264.5), "homeWeight": scale_weight(258.4), "notes": ""},
    {"date": "2025-12-24", "doctor": "Patel",    "officeWeight": scale_weight(260.9), "homeWeight": scale_weight(255.9), "notes": ""},
]

year_records = [
    {"year": "2003", "low": scale_weight(295),   "high": scale_weight(295),   "notes": ""},
    {"year": "2006", "low": scale_weight(267),   "high": scale_weight(267),   "notes": ""},
    {"year": "2013", "low": scale_weight(232),   "high": scale_weight(232),   "notes": ""},
    {"year": "2014", "low": scale_weight(275),   "high": scale_weight(275),   "notes": ""},
    {"year": "2015", "low": scale_weight(255),   "high": scale_weight(260),   "notes": ""},
    {"year": "2016", "low": scale_weight(260),   "high": scale_weight(260),   "notes": ""},
    {"year": "2017", "low": scale_weight(260),   "high": scale_weight(287),   "notes": ""},
    {"year": "2018", "low": scale_weight(255),   "high": scale_weight(260),   "notes": ""},
    {"year": "2019", "low": scale_weight(250),   "high": scale_weight(260),   "notes": ""},
    {"year": "2020", "low": scale_weight(247),   "high": scale_weight(268),   "notes": ""},
    {"year": "2021", "low": scale_weight(243),   "high": scale_weight(267),   "notes": ""},
    {"year": "2022", "low": scale_weight(237),   "high": scale_weight(256),   "notes": ""},
    {"year": "2023", "low": scale_weight(241),   "high": scale_weight(267),   "notes": ""},
    {"year": "2024", "low": scale_weight(253),   "high": scale_weight(269),   "notes": ""},
    {"year": "2025", "low": scale_weight(253),   "high": scale_weight(269),   "notes": ""},
    {"year": "2026", "low": min(fictional_weights), "high": max(fictional_weights), "notes": ""},
]

output = {
    "entries": entries,
    "goal": round(225 * scale, 1),
    "doctorVisits": doctor_visits,
    "yearRecords": year_records,
    "savedAt": "2026-04-23T19:19:29.607Z",
}

with open("weight-tracker-demo.json", "w") as f:
    json.dump(output, f, indent=2)

print(f"Generated {len(entries)} entries")
print(f"Fictional weight range: {min(fictional_weights)} - {max(fictional_weights)}")
print(f"Goal: {output['goal']}")
print("Done -> weight-tracker-demo.json")
