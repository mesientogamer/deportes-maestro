SPORTS = {
    "football": {
        "name": "1. FÚTBOL",
        "keywords": [
            "football",
            "soccer",
            "futbol",
            "fútbol"
        ]
    },

    "tennis": {
        "name": "2. TENIS",
        "keywords": [
            "tennis",
            "tenis",
            "atp",
            "wta"
        ]
    },

    "basketball": {
        "name": "3. BALONCESTO",
        "keywords": [
            "basketball",
            "baloncesto",
            "nba",
            "euroleague",
            "fiba"
        ]
    },

    "f1": {
        "name": "4. FÓRMULA 1",
        "keywords": [
            "formula 1",
            "formula1",
            "f1"
        ]
    },

    "motogp": {
        "name": "5. MOTOGP",
        "keywords": [
            "motogp",
            "moto gp",
            "motorcycle gp"
        ]
    }
}


def get_sports():
    return SPORTS


def detect_sport(text):
    text = text.lower()

    for sport_id, sport in SPORTS.items():
        for keyword in sport["keywords"]:
            if keyword in text:
                return sport_id

    return None
