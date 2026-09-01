import gzip
import xml.etree.ElementTree as ET

import requests


# ============================================================
# CONFIGURACIÓN
# ============================================================

API_BASE = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API_BASE}/channels.json"

# EPG público fusionado basado en fuentes de iptv-org/epg
EPG_URL = "https://dearbulut.github.io/iptv/epg/guide.xml.gz"


# ============================================================
# DEPORTES
# ============================================================

SPORT_KEYWORDS = {
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
        "liga portugal",
        "eredivisie",
        "uefa",
        "fifa",
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
        "masters 1000",
        "masters",
        "tennis channel",
    ],

    "basketball": [
        "basketball",
        "baloncesto",
        "nba",
        "wnba",
        "euroleague",
        "eurocup",
        "acb",
        "fiba",
        "ncaa",
        "basket",
    ],

    "formula1": [
        "formula 1",
        "formula1",
        "formula one",
        "f1",
        "grand prix",
        "gran premio",
        "gp ",
    ],

    "motogp": [
        "motogp",
        "moto gp",
        "moto2",
        "moto3",
        "motorcycle gp",
        "motorcycle grand prix",
    ],
}


# ============================================================
# SESIÓN HTTP
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/139.0 Safari/537.36"
        ),
        "Accept": "*/*",
    }
)


# ============================================================
# UTILIDADES
# ============================================================

def clean_text(value):
    return str(value or "").strip()


def detect_sport(text):
    """
    Detecta el deporte a partir del texto.
    """

    text = clean_text(text).lower()

    for sport, keywords in SPORT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                return sport

    return None


# ============================================================
# DESCARGAR JSON
# ============================================================

def download_json(url):

    response = SESSION.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DESCARGAR EPG
# ============================================================

def download_epg_xml():

    print("")
    print(
        "Descargando guía EPG fusionada..."
    )

    print(
        EPG_URL
    )

    response = SESSION.get(
        EPG_URL,
        timeout=180,
    )

    response.raise_for_status()

    data = response.content

    if not data:

        raise RuntimeError(
            "La guía EPG está vacía."
        )

    # La fuente termina en .gz,
    # pero comprobamos también los bytes.
    if (
        data[:2] == b"\x1f\x8b"
    ):

        print(
            "Descomprimiendo guía GZIP..."
        )

        data = gzip.decompress(
            data
        )

    return data


# ============================================================
# PARSEAR XML
# ============================================================

def parse_xml(data):

    if not data:
        return None

    try:

        return ET.fromstring(
            data
        )

    except Exception as error:

        print(
            f"ERROR XML: {error}"
        )

        return None


# ============================================================
# MAPA DE CANALES DEL XMLTV
# ============================================================

def build_xml_channel_map(root):

    result = {}

    if root is None:
        return result

    for xml_channel in root.findall(
        "channel"
    ):

        xml_id = clean_text(
            xml_channel.get(
                "id",
                ""
            )
        )

        if not xml_id:
            continue

        channel_name = ""

        display_name = (
            xml_channel.find(
                "display-name"
            )
        )

        if display_name is not None:

            channel_name = clean_text(
                display_name.text
            )

        result[
            xml_id
        ] = channel_name

    return result


# ============================================================
# MAPA DE CANALES DE IPTV-ORG
# ============================================================

def get_sports_channels():

    print("")
    print(
        "Descargando canales de iptv-org..."
    )

    channels = download_json(
        CHANNELS_URL
    )

    print(
        f"Canales recibidos: "
        f"{len(channels)}"
    )

    sports_channels = {}

    for channel in channels:

        if not isinstance(
            channel,
            dict
        ):
            continue

        channel_id = clean_text(
            channel.get(
                "id",
                ""
            )
        )

        if not channel_id:
            continue

        categories = channel.get(
            "categories",
            []
        )

        categories_normalized = {
            clean_text(
                category
            ).lower()
            for category in categories
        }

        if "sports" in categories_normalized:

            sports_channels[
                channel_id
            ] = channel

    print(
        f"Canales deportivos: "
        f"{len(sports_channels)}"
    )

    return sports_channels


# ============================================================
# OBTENER NOMBRE DE CANAL
# ============================================================

def get_channel_name(channel):

    if not isinstance(
        channel,
        dict
    ):
        return ""

    # Intentamos varias propiedades
    # porque la API puede tener nombres
    # diferentes según el canal.

    name = clean_text(
        channel.get(
            "name",
            ""
        )
    )

    if name:
        return name

    name = clean_text(
        channel.get(
            "alt_names",
            ""
        )
    )

    return name


# ============================================================
# EXTRAER TEXTO XML
# ============================================================

def get_xml_text(
    programme,
    tag
):

    element = programme.find(
        tag
    )

    if element is None:
        return ""

    return clean_text(
        element.text
    )


# ============================================================
# DESCARGA PRINCIPAL
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

    # ========================================================
    # 1. CANALES DEPORTIVOS
    # ========================================================

    sports_channels = (
        get_sports_channels()
    )

    if not sports_channels:

        print(
            "No se encontraron canales deportivos."
        )

        return []

    # ========================================================
    # 2. DESCARGAR EPG
    # ========================================================

    print("")

    try:

        epg_data = download_epg_xml()

    except Exception as error:

        print("")
        print(
            "ERROR DESCARGANDO EPG:"
        )

        print(
            error
        )

        return []

    print(
        f"EPG descargado: "
        f"{len(epg_data):,} bytes"
    )

    # ========================================================
    # 3. PARSEAR XML
    # ========================================================

    root = parse_xml(
        epg_data
    )

    if root is None:

        print(
            "No se pudo interpretar el XMLTV."
        )

        return []

    # ========================================================
    # 4. MAPA DE CANALES XMLTV
    # ========================================================

    xml_channels = (
        build_xml_channel_map(
            root
        )
    )

    print(
        f"Canales dentro del EPG: "
        f"{len(xml_channels)}"
    )

    # ========================================================
    # 5. BUSCAR PROGRAMAS
    # ========================================================

    all_programmes = []

    total_programmes = 0

    sports_programmes = 0

    matched_channels = set()

    print("")
    print(
        "Procesando programas EPG..."
    )

    for programme in root.findall(
        "programme"
    ):

        total_programmes += 1

        # ----------------------------------------------------
        # ID DEL CANAL XMLTV
        # ----------------------------------------------------

        xml_channel = clean_text(
            programme.get(
                "channel",
                ""
            )
        )

        if not xml_channel:
            continue

        # ----------------------------------------------------
        # MATCH DIRECTO CON IPTV-ORG
        # ----------------------------------------------------

        channel = sports_channels.get(
            xml_channel
        )

        if channel is None:
            continue

        matched_channels.add(
            xml_channel
        )

        # ----------------------------------------------------
        # HORARIO
        # ----------------------------------------------------

        start = clean_text(
            programme.get(
                "start",
                ""
            )
        )

        stop = clean_text(
            programme.get(
                "stop",
                ""
            )
        )

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        title = get_xml_text(
            programme,
            "title"
        )

        if not title:
            continue

        # ----------------------------------------------------
        # DESCRIPCIÓN
        # ----------------------------------------------------

        description = get_xml_text(
            programme,
            "desc"
        )

        # ----------------------------------------------------
        # NOMBRE DEL CANAL
        # ----------------------------------------------------

        channel_name = (
            xml_channels.get(
                xml_channel,
                ""
            )
        )

        if not channel_name:

            channel_name = (
                get_channel_name(
                    channel
                )
            )

        if not channel_name:

            channel_name = xml_channel

        # ----------------------------------------------------
        # DEPORTE
        # ----------------------------------------------------

        sport_text = (
            f"{title} "
            f"{description} "
            f"{channel_name}"
        )

        sport = detect_sport(
            sport_text
        )

        # ----------------------------------------------------
        # SI EL CANAL ES DEPORTIVO PERO
        # NO SE PUEDE IDENTIFICAR EL DEPORTE
        # ----------------------------------------------------

        if not sport:

            # Como el canal ya pertenece a
            # la categoría sports de iptv-org,
            # intentamos identificarlo por su nombre.

            sport = detect_sport(
                channel_name
            )

        # ----------------------------------------------------
        # Si sigue sin identificarse,
        # no lo descartamos.
        #
        # Se marca como football por defecto
        # SOLO para no perder canales deportivos
        # que tengan nombres genéricos.
        # ----------------------------------------------------

        if not sport:

            sport = "football"

        # ----------------------------------------------------
        # GUARDAR PROGRAMA
        # ----------------------------------------------------

        all_programmes.append(
            {
                "channel": xml_channel,
                "feed": "",
                "epg_channel": xml_channel,
                "channel_name": channel_name,
                "start": start,
                "stop": stop,
                "title": title,
                "description": description,
                "sport": sport,
                "source": EPG_URL,
                "site": "iptv-nexus",
                "lang": "",
                "live": False,
                "servers": [],
            }
        )

        sports_programmes += 1

    # ========================================================
    # RESULTADOS
    # ========================================================

    print("")
    print(
        "=========================================="
    )

    print(
        f"Programas totales en EPG: "
        f"{total_programmes:,}"
    )

    print(
        f"Canales deportivos con EPG: "
        f"{len(matched_channels):,}"
    )

    print(
        f"Programas deportivos obtenidos: "
        f"{sports_programmes:,}"
    )

    print(
        "=========================================="
    )

    return all_programmes


# ============================================================
# COMPATIBILIDAD CON MAIN.PY
# ============================================================

def parse_epg(xml_data):

    return xml_data


# ============================================================
# FILTRAR EVENTOS DEPORTIVOS
# ============================================================

def get_sport_events(programs):

    events = []

    for program in programs:

        sport = program.get(
            "sport"
        )

        if sport in SPORT_KEYWORDS:

            events.append(
                program
            )

            continue

        title = clean_text(
            program.get(
                "title",
                ""
            )
        )

        description = clean_text(
            program.get(
                "description",
                ""
            )
        )

        channel_name = clean_text(
            program.get(
                "channel_name",
                ""
            )
        )

        text = (
            title
            + " "
            + description
            + " "
            + channel_name
        )

        detected = detect_sport(
            text
        )

        if detected:

            program["sport"] = (
                detected
            )

            events.append(
                program
            )

    return events


# ============================================================
# AGRUPAR POR DEPORTE
# ============================================================

def group_events_by_sport(events):

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

        sport = event.get(
            "sport"
        )

        if sport in groups:

            groups[
                sport
            ].append(
                event
            )

    return {
        sport: groups[sport]
        for sport in order
    }


# ============================================================
# NORMALIZAR EVENTO
# ============================================================

def normalize_event(event):

    title = clean_text(
        event.get(
            "title",
            ""
        )
    )

    description = clean_text(
        event.get(
            "description",
            ""
        )
    )

    sport = event.get(
        "sport"
    )

    if not sport:

        sport = detect_sport(
            f"{title} {description}"
        )

    return {
        "id": clean_text(
            event.get(
                "id",
                ""
            )
        ),

        "sport": sport,

        "title": title,

        "description": description,

        "channel": clean_text(
            event.get(
                "channel",
                ""
            )
        ),

        "channel_name": clean_text(
            event.get(
                "channel_name",
                ""
            )
        ),

        "epg_channel": clean_text(
            event.get(
                "epg_channel",
                ""
            )
        ),

        "feed": clean_text(
            event.get(
                "feed",
                ""
            )
        ),

        "start": clean_text(
            event.get(
                "start",
                ""
            )
        ),

        "stop": clean_text(
            event.get(
                "stop",
                ""
            )
        ),

        "live": bool(
            event.get(
                "live",
                False
            )
        ),

        "servers": event.get(
            "servers",
            []
        ),

        "source": clean_text(
            event.get(
                "source",
                ""
            )
        ),

        "site": clean_text(
            event.get(
                "site",
                ""
            )
        ),

        "lang": clean_text(
            event.get(
                "lang",
                ""
            )
        ),
    }
