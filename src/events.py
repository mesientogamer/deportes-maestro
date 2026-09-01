from datetime import datetime, timezone


SPORTS = {
    "football": [
        "football",
        "soccer",
        "futbol",
        "fútbol",
        "premier league",
        "la liga",
        "champions league",
        "europa league",
        "conference league",
        "copa del rey",
        "serie a",
        "bundesliga",
        "ligue 1",
    ],
    "tennis": [
        "tennis",
        "tenis",
        "atp",
        "wta",
        "wimbledon",
        "roland garros",
        "us open",
        "australian open",
    ],
    "basketball": [
        "basketball",
        "baloncesto",
        "nba",
        "euroleague",
        "acb",
        "fiba",
    ],
    "formula1": [
        "formula 1",
        "formula1",
        "f1",
        "grand prix",
        "grand prix",
        "gp ",
    ],
    "motogp": [
        "motogp",
        "moto gp",
        "moto2",
        "moto3",
    ],
}


SPORT_NAMES = {
    "football": "FÚTBOL",
    "tennis": "TENIS",
    "basketball": "BALONCESTO",
    "formula1": "FÓRMULA 1",
    "motogp": "MOTOGP",
}


def get_current_time():
    """Devuelve la hora actual en UTC."""
    return datetime.now(timezone.utc)


def detect_sport(title, description=""):
    """
    Detecta el deporte a partir del título y descripción
    del evento.
    """

    text = (
        f"{title} {description}"
    ).lower()

    for sport, keywords in SPORTS.items():
        for keyword in keywords:
            if keyword in text:
                return sport

    return None


def normalize_event(event):
    """
    Convierte un evento procedente de la EPG
    en una estructura uniforme.
    """

    title = str(
        event.get("title", "")
    ).strip()

    description = str(
        event.get("description", "")
    ).strip()

    sport = event.get("sport")

    if not sport:
        sport = detect_sport(
            title,
            description
        )

    return {
        "id": event.get("id"),
        "sport": sport,
        "sport_name": SPORT_NAMES.get(
            sport,
            "OTROS"
        ),
        "title": title,
        "description": description,
        "channel": event.get(
            "channel",
            ""
        ),
        "start": event.get(
            "start",
            ""
        ),
        "stop": event.get(
            "stop",
            ""
        ),
        "live": bool(
            event.get("live", False)
        ),
        "servers": event.get(
            "servers",
            []
        ),
    }


def get_live_events(events):
    """
    Devuelve únicamente los eventos
    que están marcados como directos.
    """

    result = []

    for event in events:

        normalized = normalize_event(
            event
        )

        if normalized["live"]:
            result.append(
                normalized
            )

    return result


def filter_sports_events(events):
    """
    Conserva únicamente los cinco deportes
    que forman parte de la parrilla.
    """

    result = []

    for event in events:

        normalized = normalize_event(
            event
        )

        if normalized["sport"] in SPORTS:
            result.append(
                normalized
            )

    return result


def group_events_by_sport(events):
    """
    Agrupa los eventos respetando siempre
    este orden:

    1. Fútbol
    2. Tenis
    3. Baloncesto
    4. Fórmula 1
    5. MotoGP
    """

    order = [
        "football",
        "tennis",
        "basketball",
        "formula1",
        "motogp",
    ]

    groups = {
        sport: []
        for sport in order
    }

    for event in events:

        normalized = normalize_event(
            event
        )

        sport = normalized["sport"]

        if sport in groups:
            groups[sport].append(
                normalized
            )

    return {
        sport: groups[sport]
        for sport in order
    }


def add_server(event, server):
    """
    Añade una fuente/servidor a un evento
    sin duplicarlo.
    """

    normalized = normalize_event(
        event
    )

    servers = normalized["servers"]

    if server not in servers:
        servers.append(server)

    normalized["servers"] = servers

    return normalized
