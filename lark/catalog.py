"""Cities, rooms, and things to do that Lark already knows by heart.

Prices are desk estimates in USD, not live fares or bookings.
"""

from __future__ import annotations

CITIES: dict[str, dict] = {
    "lisbon": {
        "name": "Lisbon",
        "country": "Portugal",
        "iata": "LIS",
        "lat": 38.77,
        "lon": -9.13,
        "region": "europe",
        "aliases": ["lisbon", "lisboa"],
        "best_months": {4, 5, 6, 9, 10},
        "tough_months": {12, 1, 2},
        "good_season": "June is shirtsleeve weather, and the late sun stays up for the miradouros.",
        "shoulder_season": "It's mild. Bring a layer for the river wind.",
        "tough_season": "Winter is wet and green. The pastel de nata still works.",
        "hotels": [
            {"name": "Selina Secret Garden", "area": "Baixa", "style": "Hostel", "nightly": 48, "rating": 4.1, "sleeps": 2, "note": "A simple bed and a garden, so the city gets the rest of the money."},
            {"name": "Independente Bica", "area": "Bica", "style": "Hotel", "nightly": 128, "rating": 4.4, "sleeps": 2, "note": "A house-hotel with a bakery at the door and the hill right under it."},
            {"name": "The Lumiares", "area": "Príncipe Real", "style": "Apartment", "nightly": 175, "rating": 4.6, "sleeps": 3, "note": "An apartment with a kitchen, above the garden district."},
            {"name": "Memmo Alfama", "area": "Alfama", "style": "Hotel", "nightly": 230, "rating": 4.7, "sleeps": 2, "note": "Tile roofs, a small pool, and the river in the corner of the window."},
        ],
        "activities": [
            {"name": "Miradouro da Senhora do Monte", "area": "Graça", "price": 0, "per": "party", "hours": 1, "tags": ["walking", "view", "quiet"], "note": "The whole city, and it costs nothing but the climb."},
            {"name": "Pastéis de Belém", "area": "Belém", "price": 8, "per": "person", "hours": 1, "tags": ["food"], "note": "Eat the tart while it is still warm. That is the whole plan."},
            {"name": "Tram 28, early", "area": "Alfama", "price": 4, "per": "person", "hours": 1, "tags": ["walking"], "note": "Ride it before the crowds, then get off and walk down."},
            {"name": "LX Factory afternoon", "area": "Alcântara", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "food"], "note": "Bookshops, leftover warehouses, a late lunch."},
            {"name": "Sintra and Pena", "area": "Sintra", "price": 42, "per": "person", "hours": 6, "tags": ["adventure", "view"], "note": "A train and a palace in the fog. Give it a whole day."},
            {"name": "Fado in Alfama", "area": "Alfama", "price": 35, "per": "person", "hours": 2, "tags": ["nightlife", "food"], "note": "A small room, a singer, a glass of wine."},
        ],
    },
    "paris": {
        "name": "Paris",
        "country": "France",
        "iata": "CDG",
        "lat": 49.01,
        "lon": 2.55,
        "region": "europe",
        "aliases": ["paris"],
        "best_months": {5, 6, 9, 10},
        "tough_months": {1, 2, 8},
        "good_season": "Late spring and early fall are the city at an easy temperature.",
        "shoulder_season": "Gray light, good museums, fewer lines.",
        "tough_season": "August empties the bakeries. January is beautiful and cold.",
        "hotels": [
            {"name": "Generator Paris", "area": "10th", "style": "Hostel", "nightly": 62, "rating": 4.0, "sleeps": 2, "note": "A canal-side bunk or a small room when the budget is the boss."},
            {"name": "Hôtel Jeanne d'Arc", "area": "Le Marais", "style": "Hotel", "nightly": 165, "rating": 4.3, "sleeps": 2, "note": "A small Marais hotel. You are in the walkable part immediately."},
            {"name": "Hôtel Fabric", "area": "11th", "style": "Hotel", "nightly": 190, "rating": 4.5, "sleeps": 2, "note": "A former factory, quiet rooms, Oberkampf at the end of the street."},
            {"name": "The Hoxton, Paris", "area": "2nd", "style": "Hotel", "nightly": 310, "rating": 4.6, "sleeps": 2, "note": "A lobby you will actually sit in, near the old markets."},
        ],
        "activities": [
            {"name": "Walk the Marais", "area": "Le Marais", "price": 0, "per": "party", "hours": 2, "tags": ["walking"], "note": "Courtyards, falafel, a bookstore. No ticket required."},
            {"name": "Tate of the Seine picnic", "area": "the Seine", "price": 16, "per": "person", "hours": 2, "tags": ["food", "quiet"], "note": "Cheese, a baguette, a quay. Call it lunch."},
            {"name": "Musée d'Orsay, opening hour", "area": "7th", "price": 16, "per": "person", "hours": 2, "tags": ["art", "museum"], "note": "Clocks, impressionists, and a museum that used to be a station."},
            {"name": "Sainte-Chapelle", "area": "Île de la Cité", "price": 13, "per": "person", "hours": 1, "tags": ["museum"], "note": "Go up the stairs. The glass does the rest."},
            {"name": "Canal Saint-Martin at dusk", "area": "10th", "price": 18, "per": "person", "hours": 2, "tags": ["nightlife", "food"], "note": "A glass of something and the bridges lighting up."},
            {"name": "Louvre, late slot", "area": "1st", "price": 22, "per": "person", "hours": 3, "tags": ["museum", "art"], "note": "One wing, not the whole palace. Leave while you still like it."},
        ],
    },
    "rome": {
        "name": "Rome",
        "country": "Italy",
        "iata": "FCO",
        "lat": 41.8,
        "lon": 12.25,
        "region": "europe",
        "aliases": ["rome", "roma"],
        "best_months": {4, 5, 6, 9, 10},
        "tough_months": {7, 8, 1},
        "good_season": "Spring and fall let you walk at noon without negotiating with the sun.",
        "shoulder_season": "Mild enough for long walks and late dinners.",
        "tough_season": "August in Rome is hot. Midday belongs indoors, or to gelato.",
        "hotels": [
            {"name": "Generator Rome", "area": "Termini", "style": "Hostel", "nightly": 55, "rating": 4.0, "sleeps": 2, "note": "A clean, simple room near the station when the ruins are the point."},
            {"name": "Hotel Campo de' Fiori", "area": "Campo de' Fiori", "style": "Hotel", "nightly": 175, "rating": 4.4, "sleeps": 2, "note": "Wake up next to the morning market."},
            {"name": "Hotel Artemide", "area": "Repubblica", "style": "Hotel", "nightly": 210, "rating": 4.6, "sleeps": 2, "note": "A roof terrace and a proper bed between long walking days."},
            {"name": "Portrait Roma", "area": "Via Condotti", "style": "Hotel", "nightly": 480, "rating": 4.8, "sleeps": 2, "note": "The splurge: quiet, central, and a little ridiculous in the best way."},
        ],
        "activities": [
            {"name": "Trastevere after dark", "area": "Trastevere", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "nightlife"], "note": "Get lost on purpose. Eat wherever is full."},
            {"name": "Supplì from Supplizio", "area": "Centro", "price": 8, "per": "person", "hours": 1, "tags": ["food"], "note": "Fried rice, tomato, a bench. This is the snack."},
            {"name": "Colosseum, early entry", "area": "Celio", "price": 22, "per": "person", "hours": 2, "tags": ["museum", "history"], "note": "Be there when it opens. The heat and the groups come later."},
            {"name": "Villa Borghese park", "area": "Villa Borghese", "price": 0, "per": "party", "hours": 2, "tags": ["quiet", "walking"], "note": "Rent nothing. Just walk until the city feels far away."},
            {"name": "Testaccio market lunch", "area": "Testaccio", "price": 18, "per": "person", "hours": 2, "tags": ["food"], "note": "A neighborhood market, a plate of something Roman, no performance."},
            {"name": "Aperitivo in Monti", "area": "Monti", "price": 15, "per": "person", "hours": 2, "tags": ["nightlife", "food"], "note": "A spritz and the little streets behind the forum."},
        ],
    },
    "barcelona": {
        "name": "Barcelona",
        "country": "Spain",
        "iata": "BCN",
        "lat": 41.3,
        "lon": 2.08,
        "region": "europe",
        "aliases": ["barcelona", "barna"],
        "best_months": {5, 6, 9, 10},
        "tough_months": {8},
        "good_season": "May, June, and early fall are warm without the August crush.",
        "shoulder_season": "Good walking weather, and the sea is still there.",
        "tough_season": "August is hot and booked. Mornings and late dinners save it.",
        "hotels": [
            {"name": "Pars Tailor's Hostel", "area": "Sant Pere", "style": "Hostel", "nightly": 46, "rating": 4.2, "sleeps": 2, "note": "A design hostel a short walk from the old town."},
            {"name": "Praktik Vinoteca", "area": "Eixample", "style": "Hotel", "nightly": 155, "rating": 4.4, "sleeps": 2, "note": "A wine-soaked little hotel on a grid street. The beach is a metro away."},
            {"name": "Casa Bonay", "area": "Eixample", "style": "Hotel", "nightly": 195, "rating": 4.5, "sleeps": 2, "note": "A grand staircase, a rooftop, and coffee that is taken seriously."},
            {"name": "Casa Camper", "area": "El Raval", "style": "Hotel", "nightly": 280, "rating": 4.6, "sleeps": 2, "note": "Playful, central, and across from a museum."},
        ],
        "activities": [
            {"name": "El Born, no map", "area": "El Born", "price": 0, "per": "party", "hours": 2, "tags": ["walking"], "note": "Basilica at one end, bars at the other, laundry in between."},
            {"name": "Bunkers del Carmel at sunset", "area": "El Carmel", "price": 0, "per": "party", "hours": 2, "tags": ["view", "walking"], "note": "The city goes gold. Bring something to drink and a layer."},
            {"name": "Bombas at La Cova Fumada", "area": "Barceloneta", "price": 12, "per": "person", "hours": 1, "tags": ["food"], "note": "The potato bomba, eaten near the beach, no fuss."},
            {"name": "Sagrada Família", "area": "Eixample", "price": 30, "per": "person", "hours": 2, "tags": ["museum", "art"], "note": "Book a time. Look up longer than you look at your phone."},
            {"name": "Vermut hour", "area": "Sant Antoni", "price": 10, "per": "person", "hours": 1, "tags": ["food", "nightlife"], "note": "A vermouth, a snack, and the evening starting properly."},
            {"name": "Gothic Quarter morning", "area": "Barri Gòtic", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "history"], "note": "Go early, before the cruise groups, when it still feels like a neighborhood."},
        ],
    },
    "london": {
        "name": "London",
        "country": "United Kingdom",
        "iata": "LHR",
        "lat": 51.47,
        "lon": -0.45,
        "region": "europe",
        "aliases": ["london"],
        "best_months": {5, 6, 9},
        "tough_months": {1, 2, 11, 12},
        "good_season": "A long evening in May or June is London's best trick.",
        "shoulder_season": "You will wear a jacket. The museums will make up for it.",
        "tough_season": "Winter is dark by four. Lean into pubs, lights, and big museums.",
        "hotels": [
            {"name": "Generator London", "area": "King's Cross", "style": "Hostel", "nightly": 58, "rating": 4.0, "sleeps": 2, "note": "A straightforward room by the trains, and the city is all connections from here."},
            {"name": "citizenM Tower of London", "area": "Tower Hill", "style": "Hotel", "nightly": 165, "rating": 4.4, "sleeps": 2, "note": "A compact, well-designed room. The Tower is outside, not in the budget."},
            {"name": "The Hoxton, Southwark", "area": "Southwark", "style": "Hotel", "nightly": 220, "rating": 4.5, "sleeps": 2, "note": "South of the river, which is where you want dinner anyway."},
            {"name": "Zetter Townhouse", "area": "Clerkenwell", "style": "Hotel", "nightly": 260, "rating": 4.6, "sleeps": 2, "note": "Eccentric, plush, and a short walk to anything worth doing."},
        ],
        "activities": [
            {"name": "Tate Modern", "area": "Bankside", "price": 0, "per": "party", "hours": 2, "tags": ["art", "museum"], "note": "Free to enter. The view from the balcony is part of the ticket you didn't buy."},
            {"name": "Regent's Canal", "area": "Islington", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "quiet"], "note": "Narrowboats, towpaths, a coffee when you get cold."},
            {"name": "Borough Market", "area": "London Bridge", "price": 18, "per": "person", "hours": 2, "tags": ["food"], "note": "Go hungry. Leave before you have bought a second lunch."},
            {"name": "Sky Garden", "area": "the City", "price": 0, "per": "party", "hours": 1, "tags": ["view"], "note": "Book the free slot. The city looks organized from up here."},
            {"name": "Dishoom breakfast", "area": "Covent Garden", "price": 22, "per": "person", "hours": 1, "tags": ["food"], "note": "Bacon naan, chai, a queue that moves. Do it once."},
            {"name": "West End, cheap seat", "area": "Soho", "price": 35, "per": "person", "hours": 3, "tags": ["nightlife", "art"], "note": "A same-week ticket. The play matters less than being in the room."},
        ],
    },
    "tokyo": {
        "name": "Tokyo",
        "country": "Japan",
        "iata": "HND",
        "lat": 35.55,
        "lon": 139.78,
        "region": "japan",
        "aliases": ["tokyo"],
        "best_months": {3, 4, 5, 10, 11},
        "tough_months": {8, 9, 1},
        "good_season": "April is mild, and if the blossoms are out, the parks do the decorating.",
        "shoulder_season": "Comfortable walking weather and serious appetite weather.",
        "tough_season": "August is thick and hot. January is clear and sharp. Plan indoors at midday either way.",
        "hotels": [
            {"name": "Nui. Hostel & Bar", "area": "Kuramae", "style": "Hostel", "nightly": 52, "rating": 4.2, "sleeps": 2, "note": "A social hostel in a neighborhood of workshops and coffee."},
            {"name": "Hotel Gracery Shinjuku", "area": "Shinjuku", "style": "Hotel", "nightly": 145, "rating": 4.3, "sleeps": 2, "note": "Right in the neon. Convenient, and a little loud in a way you came for."},
            {"name": "Sequence Miyashita Park", "area": "Shibuya", "style": "Hotel", "nightly": 210, "rating": 4.5, "sleeps": 2, "note": "A park on the roof, Shibuya underneath, trains everywhere."},
            {"name": "Trunk (Hotel) Cat Street", "area": "Shibuya", "style": "Hotel", "nightly": 280, "rating": 4.6, "sleeps": 2, "note": "A small design hotel on the street between Shibuya and Harajuku."},
        ],
        "activities": [
            {"name": "Sensō-ji at opening", "area": "Asakusa", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "history"], "note": "Get there early. The gate is better before the snack stalls fully wake up."},
            {"name": "Yanaka backstreets", "area": "Yanaka", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "quiet"], "note": "Low houses, cemeteries, cats, a different century of the city."},
            {"name": "Tsukiji outer market", "area": "Tsukiji", "price": 20, "per": "person", "hours": 2, "tags": ["food"], "note": "Tamago, coffee, something on a stick. Breakfast, done properly."},
            {"name": "Standing sushi in Shimbashi", "area": "Shimbashi", "price": 28, "per": "person", "hours": 1, "tags": ["food"], "note": "A counter, a few pieces, no ceremony past the fish."},
            {"name": "teamLab Planets", "area": "Toyosu", "price": 32, "per": "person", "hours": 2, "tags": ["art"], "note": "You will take your shoes off and walk through water. Book ahead."},
            {"name": "A day in Kamakura", "area": "Kamakura", "price": 38, "per": "person", "hours": 7, "tags": ["walking", "history"], "note": "The train south, a great buddha, the sea at the end of the street."},
        ],
    },
    "mexico-city": {
        "name": "Mexico City",
        "country": "Mexico",
        "iata": "MEX",
        "lat": 19.44,
        "lon": -99.07,
        "region": "mexico",
        "aliases": ["mexico city", "cdmx", "mexico df", "ciudad de mexico"],
        "best_months": {3, 4, 5, 10, 11},
        "tough_months": {6, 7, 8},
        "good_season": "Spring and late fall are dry, clear, and made for walking.",
        "shoulder_season": "Mild days. Evenings cool off. Bring a jacket anyway.",
        "tough_season": "Summer brings afternoon rain. Mornings are still yours.",
        "hotels": [
            {"name": "Viajero CDMX", "area": "Roma Norte", "style": "Hostel", "nightly": 38, "rating": 4.2, "sleeps": 2, "note": "A social hostel in Roma, which is where you wanted to be anyway."},
            {"name": "The Red Tree House", "area": "Condesa", "style": "Guesthouse", "nightly": 120, "rating": 4.5, "sleeps": 2, "note": "A courtyard house on a leafy street. Breakfast is part of the charm."},
            {"name": "Condesa DF", "area": "Condesa", "style": "Hotel", "nightly": 185, "rating": 4.5, "sleeps": 2, "note": "The neighborhood's landmark hotel. The park is outside the door."},
            {"name": "Downtown Mexico", "area": "Centro", "style": "Hotel", "nightly": 240, "rating": 4.6, "sleeps": 2, "note": "A palace courtyard in the historic center, with the rooftop doing the skyline."},
        ],
        "activities": [
            {"name": "Parque México loop", "area": "Condesa", "price": 0, "per": "party", "hours": 1, "tags": ["walking", "quiet"], "note": "A green oval of a park. The day can start here."},
            {"name": "Anthropology Museum", "area": "Chapultepec", "price": 10, "per": "person", "hours": 3, "tags": ["museum", "history"], "note": "One of the great museums. Do two halls, not twelve."},
            {"name": "Coffee and a long Roma walk", "area": "Roma Norte", "price": 8, "per": "person", "hours": 2, "tags": ["walking", "food"], "note": "Bookshops, galleries, and a second coffee you did not plan."},
            {"name": "Tacos al pastor after dark", "area": "Condesa", "price": 12, "per": "person", "hours": 1, "tags": ["food", "nightlife"], "note": "Stand up, order two, then a third. This is the meal."},
            {"name": "Coyoacán and Frida's house", "area": "Coyoacán", "price": 18, "per": "person", "hours": 4, "tags": ["museum", "walking"], "note": "A blue house, a market, a slower borough. Book the museum."},
            {"name": "Xochimilco boats", "area": "Xochimilco", "price": 28, "per": "person", "hours": 3, "tags": ["adventure", "food"], "note": "Trajineras, music, a messy good afternoon on the canals."},
        ],
    },
    "reykjavik": {
        "name": "Reykjavik",
        "country": "Iceland",
        "iata": "KEF",
        "lat": 64.13,
        "lon": -21.94,
        "region": "iceland",
        "aliases": ["reykjavik", "reykjavík", "iceland"],
        "best_months": {6, 7, 8, 9},
        "tough_months": {12, 1, 2},
        "good_season": "Summer barely gets dark. You will walk at 10pm and call it afternoon.",
        "shoulder_season": "Unpredictable skies, fewer people, the pools still steam.",
        "tough_season": "Winter is short on daylight and long on weather. The lagoons earn their ticket.",
        "hotels": [
            {"name": "Kex Hostel", "area": "Harbor", "style": "Hostel", "nightly": 55, "rating": 4.2, "sleeps": 2, "note": "A social hostel in an old biscuit factory by the harbor."},
            {"name": "Kvosin Downtown", "area": "Downtown", "style": "Apartment", "nightly": 190, "rating": 4.6, "sleeps": 3, "note": "Apartment rooms in the old town, with a kitchen for expensive grocery runs."},
            {"name": "Alda Hotel", "area": "Downtown", "style": "Hotel", "nightly": 230, "rating": 4.6, "sleeps": 2, "note": "Design-forward, central, and warm in the way Iceland hotels understand."},
            {"name": "Canopy by Hilton Reykjavik", "area": "Harbor", "style": "Hotel", "nightly": 280, "rating": 4.5, "sleeps": 2, "note": "Harbor lights, a good bed, and the city a ten-minute walk away."},
        ],
        "activities": [
            {"name": "Hallgrímskirkja and the tower", "area": "Downtown", "price": 10, "per": "person", "hours": 1, "tags": ["view"], "note": "The church is free. The tower is the cheap view."},
            {"name": "Harpa, outside and in", "area": "Harbor", "price": 0, "per": "party", "hours": 1, "tags": ["walking", "art"], "note": "The concert hall looks like weather froze into glass. Walk through it."},
            {"name": "Bæjarins Beztu hot dog", "area": "Downtown", "price": 7, "per": "person", "hours": 1, "tags": ["food"], "note": "The famous stand. One is enough. Get the crisp onions."},
            {"name": "Sky Lagoon", "area": "Kópavogur", "price": 85, "per": "person", "hours": 3, "tags": ["quiet"], "note": "The ritual soak. It is the expensive hour and it is worth naming out loud."},
            {"name": "Golden Circle day", "area": "the countryside", "price": 110, "per": "person", "hours": 8, "tags": ["adventure", "view"], "note": "Geysers, a waterfall, a rift in the earth. A full day, a real tour."},
            {"name": "A rye bar in the evening", "area": "Downtown", "price": 22, "per": "person", "hours": 2, "tags": ["nightlife", "food"], "note": "Small bars, wool coats, a short walk home in the wind."},
        ],
    },
    "new-orleans": {
        "name": "New Orleans",
        "country": "United States",
        "iata": "MSY",
        "lat": 29.99,
        "lon": -90.26,
        "region": "domestic",
        "aliases": ["new orleans", "nola"],
        "best_months": {3, 4, 11},
        "tough_months": {6, 7, 8},
        "good_season": "Spring and November are warm, walkable, and festival-adjacent.",
        "shoulder_season": "You'll be fine in a light jacket and an ambitious appetite.",
        "tough_season": "Summer is thick. Stay in the shade, eat cold things, go out after dark.",
        "hotels": [
            {"name": "India House Hostel", "area": "Mid-City", "style": "Hostel", "nightly": 35, "rating": 4.0, "sleeps": 2, "note": "A backyard pool and a bunk. The Quarter is a streetcar away."},
            {"name": "International House", "area": "CBD", "style": "Hotel", "nightly": 145, "rating": 4.3, "sleeps": 2, "note": "A stylish room downtown, walkable to the river and the Quarter."},
            {"name": "Hotel Peter and Paul", "area": "Marigny", "style": "Hotel", "nightly": 210, "rating": 4.6, "sleeps": 2, "note": "A converted church complex in the Marigny. Frenchmen Street is close."},
            {"name": "The Chloe", "area": "Garden District", "style": "Hotel", "nightly": 265, "rating": 4.6, "sleeps": 2, "note": "A Garden District house with a pool. The streetcar passes the corner."},
        ],
        "activities": [
            {"name": "Garden District walk", "area": "Garden District", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "quiet"], "note": "Porches, oaks, and no agenda. Ride the streetcar one way."},
            {"name": "Streetcar down St. Charles", "area": "St. Charles", "price": 3, "per": "person", "hours": 1, "tags": ["walking"], "note": "The cheapest sightseeing in town. Sit on the right."},
            {"name": "Beignets and coffee", "area": "French Quarter", "price": 9, "per": "person", "hours": 1, "tags": ["food"], "note": "Powdered sugar on your shirt means you did it correctly."},
            {"name": "A po'boy at Parkway", "area": "Mid-City", "price": 16, "per": "person", "hours": 1, "tags": ["food"], "note": "Dressed. Eat it before you get back on the streetcar."},
            {"name": "Frenchmen Street", "area": "Marigny", "price": 15, "per": "person", "hours": 3, "tags": ["nightlife"], "note": "Music spilling out of small rooms. Duck into whichever sounds right."},
            {"name": "Cemetery and neighborhood tour", "area": "Treme", "price": 28, "per": "person", "hours": 2, "tags": ["history", "walking"], "note": "Go with a local guide. The city is not a backdrop."},
        ],
    },
    "marrakech": {
        "name": "Marrakech",
        "country": "Morocco",
        "iata": "RAK",
        "lat": 31.61,
        "lon": -8.04,
        "region": "morocco",
        "aliases": ["marrakech", "marrakesh"],
        "best_months": {3, 4, 5, 10, 11},
        "tough_months": {7, 8},
        "good_season": "Spring and fall are warm by day and kind at night, which is when the square wakes up.",
        "shoulder_season": "Bright and busy. A courtyard to hide in is the right kind of room.",
        "tough_season": "July and August are seriously hot. Mornings, riads, and late dinners.",
        "hotels": [
            {"name": "Equity Point Marrakech", "area": "Medina", "style": "Hostel", "nightly": 28, "rating": 4.1, "sleeps": 2, "note": "A courtyard hostel inside the medina when the riad can wait."},
            {"name": "Riad Kniza", "area": "Medina", "style": "Riad", "nightly": 140, "rating": 4.7, "sleeps": 2, "note": "A historic riad: courtyard, antiques, and quiet a turn off the souk."},
            {"name": "El Fenn", "area": "Medina", "style": "Riad", "nightly": 250, "rating": 4.7, "sleeps": 2, "note": "Rooftops, color, and a pool hidden above the lanes."},
            {"name": "La Mamounia", "area": "Hivernage", "style": "Palace", "nightly": 520, "rating": 4.8, "sleeps": 2, "note": "The palace. Gardens, history, and a bill that knows what it is."},
        ],
        "activities": [
            {"name": "Jemaa el-Fnaa at dusk", "area": "Medina", "price": 0, "per": "party", "hours": 2, "tags": ["walking", "nightlife", "food"], "note": "Smoke, drums, juice stalls, the whole city in one square."},
            {"name": "A morning in the souks", "area": "Medina", "price": 0, "per": "party", "hours": 2, "tags": ["walking"], "note": "Get lost while you are fresh. Buy spices only if you actually cook."},
            {"name": "Bahia Palace", "area": "Medina", "price": 8, "per": "person", "hours": 1, "tags": ["history", "museum"], "note": "Courtyards and tile. Go when it opens."},
            {"name": "Jardin Majorelle", "area": "Ville Nouvelle", "price": 18, "per": "person", "hours": 1, "tags": ["art", "quiet"], "note": "Blue walls, a cactus garden, a timed ticket."},
            {"name": "Rooftop breakfast", "area": "Medina", "price": 14, "per": "person", "hours": 1, "tags": ["food"], "note": "Mint tea, bread, a view of satellite dishes and storks."},
            {"name": "Hammam hour", "area": "Medina", "price": 30, "per": "person", "hours": 2, "tags": ["quiet"], "note": "Steam, rest, and a reset in the middle of a loud city."},
        ],
    },
}

ORIGINS: dict[str, dict] = {
    "new-york": {"name": "New York", "country": "United States", "iata": "JFK", "lat": 40.64, "lon": -73.78, "aliases": ["new york", "new york city", "nyc", "jfk"]},
    "boston": {"name": "Boston", "country": "United States", "iata": "BOS", "lat": 42.36, "lon": -71.02, "aliases": ["boston"]},
    "chicago": {"name": "Chicago", "country": "United States", "iata": "ORD", "lat": 41.97, "lon": -87.91, "aliases": ["chicago"]},
    "los-angeles": {"name": "Los Angeles", "country": "United States", "iata": "LAX", "lat": 33.94, "lon": -118.41, "aliases": ["los angeles", "la", "l.a."]},
    "miami": {"name": "Miami", "country": "United States", "iata": "MIA", "lat": 25.8, "lon": -80.29, "aliases": ["miami"]},
    "san-francisco": {"name": "San Francisco", "country": "United States", "iata": "SFO", "lat": 37.62, "lon": -122.38, "aliases": ["san francisco", "sf", "sfo"]},
    "seattle": {"name": "Seattle", "country": "United States", "iata": "SEA", "lat": 47.45, "lon": -122.31, "aliases": ["seattle"]},
    "austin": {"name": "Austin", "country": "United States", "iata": "AUS", "lat": 30.19, "lon": -97.67, "aliases": ["austin"]},
    "atlanta": {"name": "Atlanta", "country": "United States", "iata": "ATL", "lat": 33.64, "lon": -84.43, "aliases": ["atlanta"]},
    "washington": {"name": "Washington", "country": "United States", "iata": "DCA", "lat": 38.85, "lon": -77.04, "aliases": ["washington", "washington dc", "dc", "d.c."]},
}

# A destination can also be a place you leave from.
for _slug, _city in CITIES.items():
    ORIGINS.setdefault(
        _slug,
        {
            "name": _city["name"],
            "country": _city["country"],
            "iata": _city["iata"],
            "lat": _city["lat"],
            "lon": _city["lon"],
            "aliases": list(_city["aliases"]),
        },
    )

UNSUPPORTED = {
    "bali": "Bali",
    "hawaii": "Hawaii",
    "honolulu": "Honolulu",
    "cancun": "Cancún",
    "dubai": "Dubai",
    "bangkok": "Bangkok",
    "seoul": "Seoul",
    "sydney": "Sydney",
    "berlin": "Berlin",
    "amsterdam": "Amsterdam",
    "prague": "Prague",
    "athens": "Athens",
    "dublin": "Dublin",
    "vegas": "Las Vegas",
    "las vegas": "Las Vegas",
    "miami beach": "Miami",
    "florence": "Florence",
    "venice": "Venice",
    "madrid": "Madrid",
    "porto": "Porto",
    "kyoto": "Kyoto",
    "osaka": "Osaka",
    "singapore": "Singapore",
    "cape town": "Cape Town",
}


def destination(slug: str | None) -> dict | None:
    if not slug:
        return None
    return CITIES.get(slug)


def origin(slug: str | None) -> dict | None:
    if not slug:
        return None
    return ORIGINS.get(slug)


def place(slug: str | None) -> dict | None:
    return destination(slug) or origin(slug)


def alias_index() -> list[tuple[str, str, str]]:
    """Longest-first aliases: (alias, slug, role)."""
    rows: list[tuple[str, str, str]] = []
    for slug, city in CITIES.items():
        for alias in city["aliases"]:
            rows.append((alias, slug, "either"))
    for slug, city in ORIGINS.items():
        if slug in CITIES:
            continue
        for alias in city["aliases"]:
            rows.append((alias, slug, "origin"))
    rows.sort(key=lambda row: len(row[0]), reverse=True)
    return rows


ALIASES = alias_index()


def destination_names() -> list[str]:
    return [city["name"] for city in CITIES.values()]
