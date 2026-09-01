import gzip
import io
import xml.etree.ElementTree as ET
import requests


EPG_URL = "https://iptv-org.github.io/epg/guides/merged.xml.gz"


def download_epg():
    """
    Descarga la EPG comprimida y devuelve su contenido XML.
    """

    response = requests.get(
        EPG_URL,
        timeout=120,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    with gzip.GzipFile(
        fileobj=io.BytesIO(response.content)
    ) as compressed:

        return compressed.read()


def parse_epg(xml_data):
    """
    Convierte la EPG XML en una lista de programas.
    """

    root = ET.fromstring(xml_data)

    programs = []

    for programme in root.findall("programme"):

        channel = programme.get(
            "channel",
            ""
        )

        start = programme.get(
            "start",
            ""
        )

        stop = programme.get(
            "stop",
            ""
        )

        title_element = programme.find(
            "title"
        )

        desc_element = programme.find(
            "desc"
        )

        title = ""

        if title_element is not None:
            title = (
                title_element.text or ""
            ).strip()

        description = ""

        if desc_element is not None:
            description = (
                desc_element.text or ""
            ).strip()

        if not channel or not title:
            continue

        programs.append({
            "channel": channel,
            "start": start,
            "stop": stop,
            "title": title,
            "description": description,
        })

    return programs


def get_sport_events(programs):
    """
    Busca eventos deportivos en la programación.
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
            program["title"]
            + " "
            + program["description"]
        ).lower()

        if any(
            keyword in text
            for keyword in keywords
        ):
            events.append(program)

    return events
