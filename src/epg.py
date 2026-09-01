import xml.etree.ElementTree as ET
from pathlib import Path


BASE_DIR = Path(
    __file__
).resolve().parent.parent

GUIDE_FILE = (
    BASE_DIR
    / "output"
    / "guide.xml"
)


def clean(value):
    return str(
        value or ""
    ).strip()


def download_epg():

    print("")
    print(
        "============================================================"
    )
    print(
        "LEYENDO EPG GENERADO POR IPTV-ORG/EPG"
    )
    print(
        "============================================================"
    )

    if not GUIDE_FILE.exists():

        print(
            "ERROR: No existe:"
        )

        print(
            GUIDE_FILE
        )

        return []

    print(
        f"Archivo EPG encontrado: "
        f"{GUIDE_FILE}"
    )

    try:

        tree = ET.parse(
            GUIDE_FILE
        )

        root = tree.getroot()

    except Exception as error:

        print(
            f"ERROR leyendo guide.xml: "
            f"{error}"
        )

        return []

    # --------------------------------------------------------
    # Nombres de canales
    # --------------------------------------------------------

    channel_names = {}

    for channel in root.findall(
        "channel"
    ):

        channel_id = clean(
            channel.get(
                "id"
            )
        )

        if not channel_id:
            continue

        display = channel.find(
            "display-name"
        )

        name = ""

        if display is not None:
            name = clean(
                display.text
            )

        channel_names[
            channel_id
        ] = name

    # --------------------------------------------------------
    # Programas
    # --------------------------------------------------------

    programs = []

    total = 0

    for programme in root.findall(
        "programme"
    ):

        total += 1

        channel_id = clean(
            programme.get(
                "channel"
            )
        )

        if not channel_id:
            continue

        start = clean(
            programme.get(
                "start"
            )
        )

        stop = clean(
            programme.get(
                "stop"
            )
        )

        title_element = (
            programme.find(
                "title"
            )
        )

        if title_element is None:
            continue

        title = clean(
            title_element.text
        )

        if not title:
            continue

        description_element = (
            programme.find(
                "desc"
            )
        )

        description = ""

        if description_element is not None:

            description = clean(
                description_element.text
            )

        channel_name = (
            channel_names.get(
                channel_id,
                channel_id
            )
        )

        programs.append(
            {
                "channel": channel_id,

                "epg_channel": channel_id,

                "channel_name": channel_name,

                "feed": "",

                "start": start,

                "stop": stop,

                "title": title,

                "description": description,

                "live": False,

                "servers": [],
            }
        )

    print(
        f"Programas XMLTV totales: "
        f"{total}"
    )

    print(
        f"Programas cargados: "
        f"{len(programs)}"
    )

    print(
        "============================================================"
    )

    return programs


def parse_epg(data):

    return data
