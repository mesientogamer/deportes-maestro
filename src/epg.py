import gzip
import xml.etree.ElementTree as ET

import requests


API_BASE = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API_BASE}/channels.json"
GUIDES_URL = f"{API_BASE}/guides.json"


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def download_json(url):
    response = requests.get(
        url,
        timeout=120,
        headers=HEADERS
    )

    response.raise_for_status()

    return response.json()


def download_epg():
    """
    Descarga las guías EPG de los canales deportivos.

    Compatible con la estructura actual de guides.json,
    donde las fuentes están dentro de guides[].sources[].
    """

    print("Descargando información de canales...")

    channels = download_json(CHANNELS_URL)

    print(
        f"Canales recibidos: {len(channels)}"
    )

    # -------------------------------------------------
    # 1. Obtener canales deportivos
    # -------------------------------------------------

    sports_channel_ids = set()

    for channel in channels:

        channel_id = channel.get("id")

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
            sports_channel_ids.add(channel_id)

    print(
        f"Canales deportivos: "
        f"{len(sports_channel_ids)}"
    )

    # -------------------------------------------------
    # 2. Descargar índice de EPG
    # -------------------------------------------------

    print("Descargando índice de EPG...")

    guides = download_json(GUIDES_URL)

    print(
        f"Entradas EPG recibidas: "
        f"{len(guides)}"
    )

    # -------------------------------------------------
    # 3. Obtener TODAS las fuentes EPG deportivas
    # -------------------------------------------------

    guide_sources = {}

    for guide in guides:

        channel_id = guide.get("channel")

        if not channel_id:
            continue

        if channel_id not in sports_channel_ids:
            continue

        site_id = guide.get(
            "site_id",
            ""
        )

        site_name = guide.get(
            "site_name",
            ""
        )

        feed = guide.get(
            "feed"
        )

        sources = guide.get(
            "sources",
            []
        )

        for source in sources:

            url = source.get("url")

            if not url:
                continue

            if url not in guide_sources:
                guide_sources[url] = []

            guide_sources[url].append({
                "channel": channel_id,
                "feed": feed,
                "site_id": site_id,
                "site_name": site_name
            })

    print(
        f"Fuentes EPG deportivas únicas: "
        f"{len(guide_sources)}"
    )

    # -------------------------------------------------
    # 4. Descargar todas las fuentes
    # -------------------------------------------------

    all_programmes = []

    for index, (url, guide_info) in enumerate(
        guide_sources.items(),
        start=1
    ):

        print(
            f"EPG {index}/{len(guide_sources)}: "
            f"{url}"
        )

        try:

            response = requests.get(
                url,
                timeout=90,
                headers=HEADERS
            )

            if response.status_code != 200:

                print(
                    f" Saltada: HTTP "
                    f"{response.status_code}"
                )

                continue

            data = response.content

            # Algunas fuentes vienen comprimidas.
            if (
                url.endswith(".gz")
                or response.headers.get(
                    "Content-Type",
                    ""
                ).startswith(
                    "application/gzip"
                )
            ):

                try:
                    data = gzip.decompress(
                        data
                    )
                except Exception:
                    pass

            root = ET.fromstring(data)

            # -------------------------------------------------
            # Crear relación entre ID de la EPG y canal IPTV
            # -------------------------------------------------

            channel_map = {}

            for channel_element in root.findall(
                "channel"
            ):

                xml_channel_id = (
                    channel_element.get(
                        "id",
                        ""
                    )
                )

                if not xml_channel_id:
                    continue

                names = []

                for display_name in channel_element.findall(
                    "display-name"
                ):

                    name = (
                        display_name.text
                        or ""
                    ).strip()

                    if name:
                        names.append(name)

                channel_map[
                    xml_channel_id
                ] = names

            # -------------------------------------------------
            # Leer programas
            # -------------------------------------------------

            for programme in root.findall(
                "programme"
            ):

                xml_channel = programme.get(
                    "channel",
                    ""
                )

                if not xml_channel:
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

                # Intentamos asociar el ID de la EPG
                # con el canal deportivo de guides.json.
                matched_guide = None

                for guide in guide_info:

                    site_id = str(
                        guide.get(
                            "site_id",
                            ""
                        )
                    )

                    if (
                        site_id
                        and xml_channel == site_id
                    ):
                        matched_guide = guide
                        break

                # Si no encontramos coincidencia
                # exacta, usamos la primera guía
                # asociada a esta fuente.
                if matched_guide is None:
                    matched_guide = guide_info[0]

                all_programmes.append({
                    "channel": matched_guide.get(
                        "channel",
                        ""
                    ),
                    "feed": matched_guide.get(
                        "feed"
                    ),
                    "epg_channel": xml_channel,
                    "channel_name": matched_guide.get(
                        "site_name",
                        ""
                    ),
                    "start": start,
                    "stop": stop,
                    "title": title,
                    "description": description
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
    """

    return xml_data


def get_sport_events(programs):
    """
    Devuelve los programas deportivos.

    La detección se realiza por título,
    descripción y nombre del canal.
    """

    keywords = [
        # Fútbol
        "football",
        "soccer",
        "futbol",
        "fútbol",
        "premier league",
        "la liga",
        "champions",
        "europa league",
        "conference league",
        "serie a",
        "bundesliga",
        "ligue 1",
        "copa del rey",

        # Tenis
        "tennis",
        "tenis",
        "atp",
        "wta",
        "wimbledon",
        "roland garros",
        "us open",

        # Baloncesto
        "basketball",
        "baloncesto",
        "nba",
        "euroleague",
        "eurobasket",
        "fiba",
        "acb",

        # Fórmula 1
        "formula 1",
        "formula1",
        "f1",
        "grand prix",
        "grand prix",

        # MotoGP
        "motogp",
        "moto gp",
        "moto2",
        "moto3",
        "motorcycle gp"
    ]

    events = []

    for program in programs:

        text = (
            str(
                program.get(
                    "title",
                    ""
                )
            )
            + " "
            + str(
                program.get(
                    "description",
                    ""
                )
            )
            + " "
            + str(
                program.get(
                    "channel_name",
                    ""
                )
            )
        ).lower()

        if any(
            keyword in text
            for keyword in keywords
        ):

            events.append(
                program
            )

    return events
