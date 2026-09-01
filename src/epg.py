import gzip
import io
import xml.etree.ElementTree as ET

import requests


API_BASE = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API_BASE}/channels.json"
GUIDES_URL = f"{API_BASE}/guides.json"


def download_json(url):
    response = requests.get(
        url,
        timeout=120,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    return response.json()


def download_epg():
    """
    Obtiene las guías EPG disponibles para canales deportivos.

    No utiliza merged.xml.gz porque esa ruta ya no es
    una fuente válida para este proyecto.
    """

    print("Descargando información de canales...")

    channels = download_json(
        CHANNELS_URL
    )

    print(
        f"Canales recibidos: {len(channels)}"
    )

    # IDs de canales deportivos.
    sports_channel_ids = set()

    for channel in channels:

        channel_id = channel.get(
            "id"
        )

        categories = channel.get(
            "categories",
            []
        )

        if not channel_id:
            continue

        categories_normalized = {
            str(category).lower()
            for category in categories
        }

        if "sports" in categories_normalized:
            sports_channel_ids.add(
                channel_id
            )

    print(
        f"Canales deportivos: "
        f"{len(sports_channel_ids)}"
    )

    print("Descargando índice de EPG...")

    guides = download_json(
        GUIDES_URL
    )

    print(
        f"Entradas EPG recibidas: "
        f"{len(guides)}"
    )

    # Guardamos solamente las guías asociadas
    # a canales deportivos.
    guide_urls = {}

    for guide in guides:

        channel_id = guide.get(
            "channel"
        )

        url = guide.get(
            "url"
        )

        if not channel_id or not url:
            continue

        if channel_id not in sports_channel_ids:
            continue

        guide_urls.setdefault(
            url,
            set()
        ).add(channel_id)

    print(
        f"Guías deportivas únicas: "
        f"{len(guide_urls)}"
    )

    all_programmes = []

    # Limitamos el número de guías por ejecución
    # para evitar que una actualización automática
    # descargue miles de archivos innecesariamente.
    max_guides = 100

    selected_guides = list(
        guide_urls.items()
    )[:max_guides]

    for index, (url, channel_ids) in enumerate(
        selected_guides,
        start=1
    ):

        print(
            f"EPG {index}/{len(selected_guides)}: "
            f"{url}"
        )

        try:

            response = requests.get(
                url,
                timeout=60,
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            if response.status_code != 200:
                print(
                    f" Saltada: HTTP "
                    f"{response.status_code}"
                )
                continue

            data = response.content

            # Las guías pueden estar comprimidas
            # o ser XML normal.
            if url.endswith(".gz"):
                data = gzip.decompress(
                    data
                )

            root = ET.fromstring(
                data
            )

            for programme in root.findall(
                "programme"
            ):

                channel = programme.get(
                    "channel",
                    ""
                )

                if channel not in channel_ids:
                    continue

                start = programme.get(
                    "start",
                    ""
                )

                stop = programme.get(
                    "stop",
                    ""
                )

                title_element = (
                    programme.find("title")
                )

                desc_element = (
                    programme.find("desc")
                )

                title = ""

                if title_element is not None:
                    title = (
                        title_element.text
                        or ""
                    ).strip()

                description = ""

                if desc_element is not None:
                    description = (
                        desc_element.text
                        or ""
                    ).strip()

                if not title:
                    continue

                all_programmes.append({
                    "channel": channel,
                    "start": start,
                    "stop": stop,
                    "title": title,
                    "description": description,
                })

        except Exception as error:

            print(
                f" Error leyendo EPG: "
                f"{error}"
            )

    print(
        f"Programas EPG obtenidos: "
        f"{len(all_programmes)}"
    )

    return all_programmes


def parse_epg(xml_data):
    """
    Compatibilidad con main.py.

    download_epg() ya devuelve los programas
    preparados, por lo que simplemente los devuelve.
    """

    return xml_data


def get_sport_events(programs):
    """
    Filtra programas con indicios deportivos.
    """

    keywords = [
        "football",
        "soccer",
        "futbol",
        "fútbol",
        "tennis",
        "tenis",
        "atp",
        "wta",
        "basketball",
        "baloncesto",
        "nba",
        "formula 1",
        "formula1",
        "f1",
        "motogp",
        "moto gp",
    ]

    events = []

    for program in programs:

        text = (
            program.get("title", "")
            + " "
            + program.get("description", "")
        ).lower()

        if any(
            keyword in text
            for keyword in keywords
        ):
            events.append(program)

    return events
