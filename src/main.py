import gzip
import xml.etree.ElementTree as ET

import requests


# ============================================================
# FUENTES
# ============================================================

CHANNELS_URL = (
    "https://iptv-org.github.io/api/channels.json"
)

# EPG XMLTV fusionado basado en iptv-org
MERGED_EPG_URL = (
    "https://dearbulut.github.io/"
    "iptv/epg/guide.xml.gz"
)


# ============================================================
# HTTP
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# ============================================================
# DESCARGAR JSON
# ============================================================

def download_json(url):

    response = SESSION.get(
        url,
        timeout=120
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# LIMPIAR TEXTO
# ============================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# DESCARGAR EPG
# ============================================================

def download_epg():

    print("")
    print(
        "=========================================="
    )
    print(
        " OBTENIENDO PROGRAMACIÓN"
    )
    print(
        "=========================================="
    )
    print("")

    # --------------------------------------------------------
    # 1. CANALES DE IPTVO-RG
    # --------------------------------------------------------

    print(
        "Descargando información de canales..."
    )

    channels = download_json(
        CHANNELS_URL
    )

    print(
        f"Canales recibidos: "
        f"{len(channels)}"
    )

    # --------------------------------------------------------
    # 2. IDENTIFICAR CANALES DEPORTIVOS
    # --------------------------------------------------------

    sports_channels = {}

    for channel in channels:

        if not isinstance(
            channel,
            dict
        ):
            continue

        channel_id = clean(
            channel.get(
                "id"
            )
        )

        if not channel_id:
            continue

        categories = channel.get(
            "categories",
            []
        )

        categories = [
            clean(category).lower()
            for category in categories
        ]

        if "sports" not in categories:
            continue

        sports_channels[
            channel_id
        ] = channel

    print(
        f"Canales deportivos: "
        f"{len(sports_channels)}"
    )

    # --------------------------------------------------------
    # 3. DESCARGAR EPG XMLTV
    # --------------------------------------------------------

    print("")
    print(
        "Descargando EPG XMLTV fusionado..."
    )

    print(
        MERGED_EPG_URL
    )

    try:

        response = SESSION.get(
            MERGED_EPG_URL,
            timeout=300
        )

        response.raise_for_status()

    except Exception as error:

        print("")
        print(
            "ERROR descargando EPG:"
        )

        print(
            error
        )

        return []

    data = response.content

    print(
        f"EPG descargado: "
        f"{len(data):,} bytes"
    )

    # --------------------------------------------------------
    # 4. DESCOMPRIMIR
    # --------------------------------------------------------

    try:

        data = gzip.decompress(
            data
        )

        print(
            f"EPG descomprimido: "
            f"{len(data):,} bytes"
        )

    except Exception:

        # Puede venir sin gzip
        print(
            "El archivo no estaba comprimido "
            "o ya estaba descomprimido."
        )

    # --------------------------------------------------------
    # 5. PARSEAR XML
    # --------------------------------------------------------

    print("")
    print(
        "Analizando XMLTV..."
    )

    try:

        root = ET.fromstring(
            data
        )

    except Exception as error:

        print("")
        print(
            "ERROR leyendo XMLTV:"
        )

        print(
            error
        )

        return []

    # --------------------------------------------------------
    # 6. MAPA DE CANALES DEL EPG
    # --------------------------------------------------------

    xml_channels = {}

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

        display_name = ""

        element = channel.find(
            "display-name"
        )

        if element is not None:

            display_name = clean(
                element.text
            )

        xml_channels[
            channel_id
        ] = display_name

    print(
        f"Canales dentro del EPG: "
        f"{len(xml_channels)}"
    )

    # --------------------------------------------------------
    # 7. CRUZAR CON CANALES DEPORTIVOS
    # --------------------------------------------------------

    matched_channels = {}

    for channel_id in sports_channels:

        if channel_id in xml_channels:

            matched_channels[
                channel_id
            ] = sports_channels[
                channel_id
            ]

    print(
        f"Canales deportivos con EPG: "
        f"{len(matched_channels)}"
    )

    # --------------------------------------------------------
    # 8. PROGRAMAS
    # --------------------------------------------------------

    programmes = []

    for programme in root.findall(
        "programme"
    ):

        channel_id = clean(
            programme.get(
                "channel"
            )
        )

        if not channel_id:
            continue

        # Solo canales deportivos
        if channel_id not in matched_channels:
            continue

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        title_element = programme.find(
            "title"
        )

        if title_element is None:
            continue

        title = clean(
            title_element.text
        )

        if not title:
            continue

        # ----------------------------------------------------
        # DESCRIPCIÓN
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # FECHAS
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # DATOS DEL CANAL
        # ----------------------------------------------------

        channel_data = matched_channels[
            channel_id
        ]

        channel_name = clean(
            channel_data.get(
                "name"
            )
        )

        # ----------------------------------------------------
        # DEPORTE
        #
        # No dependemos únicamente de esto porque
        # main.py volverá a detectar el deporte.
        # ----------------------------------------------------

        programmes.append({

            "id": (
                f"{channel_id}_"
                f"{start}_"
                f"{title}"
            ),

            # MUY IMPORTANTE:
            # Este ID debe coincidir con streams.json
            "channel": channel_id,

            "feed": None,

            "epg_channel": channel_id,

            "channel_name": channel_name,

            "start": start,

            "stop": stop,

            "title": title,

            "description": description,

            "sport": None,

            "live": True,

            "servers": [],

        })

    # --------------------------------------------------------
    # 9. RESULTADO
    # --------------------------------------------------------

    print("")
    print(
        "=========================================="
    )

    print(
        f"Programas deportivos obtenidos: "
        f"{len(programmes)}"
    )

    print(
        "=========================================="
    )

    return programmes


# ============================================================
# PARSE_EPG
# ============================================================

def parse_epg(epg_data):

    # download_epg() ya devuelve una lista
    # de programas completamente procesada.

    if epg_data is None:
        return []

    if isinstance(
        epg_data,
        list
    ):
        return epg_data

    return []


# ============================================================
# FUNCIONES DE COMPATIBILIDAD
# ============================================================

def get_sport_events(
    programs
):

    return programs


def group_events_by_sport(
    events
):

    groups = {
        "football": [],
        "tennis": [],
        "basketball": [],
        "formula1": [],
        "motogp": [],
    }

    for event in events:

        sport = event.get(
            "sport"
        )

        if sport in groups:

            groups[
                sport
            ].append(
                event
            )

    return groups


def normalize_event(
    event
):

    return event


def get_live_events(
    events
):

    return [
        event
        for event in events
        if event.get(
            "live",
            False
        )
    ]


def filter_sports_events(
    events
):

    return events


def add_server(
    event,
    server
):

    if "servers" not in event:

        event["servers"] = []

    if server not in event[
        "servers"
    ]:

        event[
            "servers"
        ].append(
            server
        )

    return event
