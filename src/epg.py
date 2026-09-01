import gzip
import xml.etree.ElementTree as ET

import requests


# ============================================================
# CONFIGURACIÓN
# ============================================================

API_BASE = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API_BASE}/channels.json"
GUIDES_URL = f"{API_BASE}/guides.json"


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
        "gp ",
    ],

    "motogp": [
        "motogp",
        "moto gp",
        "moto2",
        "moto3",
        "motorcycle gp",
    ],
}


# ============================================================
# DESCARGA JSON
# ============================================================

def download_json(url):
    """
    Descarga un JSON desde una URL.
    """

    response = requests.get(
        url,
        timeout=120,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DETECCIÓN DE DEPORTE
# ============================================================

def detect_sport(text):
    """
    Detecta el deporte a partir del texto.
    """

    text = str(text or "").lower()

    for sport, keywords in SPORT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                return sport

    return None


# ============================================================
# DESCARGA EPG
# ============================================================

def download_epg():
    """
    Descarga la información EPG de los canales deportivos.

    Utiliza:
        channels.json
        guides.json

    Después descarga todas las guías EPG asociadas
    a canales deportivos.
    """

    print("")
    print("==========================================")
    print(" OBTENIENDO PROGRAMACIÓN")
    print("==========================================")
    print("")

    # --------------------------------------------------------
    # 1. CANALES
    # --------------------------------------------------------

    print("Descargando información de canales...")

    channels = download_json(
        CHANNELS_URL
    )

    print(
        f"Canales recibidos: {len(channels)}"
    )

    # --------------------------------------------------------
    # CANALES DEPORTIVOS
    # --------------------------------------------------------

    sports_channels = {}

    for channel in channels:

        channel_id = channel.get(
            "id"
        )

        if not channel_id:
            continue

        categories = channel.get(
            "categories",
            []
        )

        categories_normalized = {
            str(category).lower()
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

    if not sports_channels:

        print(
            "No se encontraron canales deportivos."
        )

        return []

    # --------------------------------------------------------
    # 2. GUÍAS
    # --------------------------------------------------------

    print("")
    print("Descargando índice de EPG...")

    guides = download_json(
        GUIDES_URL
    )

    print(
        f"Entradas EPG recibidas: "
        f"{len(guides)}"
    )

    # --------------------------------------------------------
    # MOSTRAR ALGUNAS GUÍAS PARA DEBUG
    # --------------------------------------------------------

    print("")
    print("========== PRIMERAS GUÍAS ==========")

    for guide in guides[:10]:

        print(
            guide
        )

    print(
        "===================================="
    )
    print("")

    # --------------------------------------------------------
    # 3. BUSCAR TODAS LAS GUÍAS DEPORTIVAS
    # --------------------------------------------------------

    guide_map = {}

    for guide in guides:

        if not isinstance(
            guide,
            dict
        ):
            continue

        channel_id = guide.get(
            "channel"
        )

        url = guide.get(
            "url"
        )

        if not url:
            continue

        # Solo nos interesan canales deportivos.
        if (
            channel_id
            and channel_id not in sports_channels
        ):
            continue

        # Guardamos todas las guías.
        if url not in guide_map:

            guide_map[url] = []

        guide_map[url].append(
            guide
        )

    print(
        f"Fuentes EPG deportivas únicas: "
        f"{len(guide_map)}"
    )

    if not guide_map:

        print("")
        print(
            "ATENCIÓN: no se encontraron "
            "URLs EPG para los canales deportivos."
        )
        print(
            "Se devolverán 0 programas."
        )

        return []

    # --------------------------------------------------------
    # 4. DESCARGAR TODAS LAS GUÍAS
    # --------------------------------------------------------

    all_programmes = []

    total_guides = len(
        guide_map
    )

    for index, (
        url,
        guide_info
    ) in enumerate(
        guide_map.items(),
        start=1
    ):

        print("")
        print(
            f"EPG {index}/{total_guides}"
        )

        print(
            url
        )

        try:

            response = requests.get(
                url,
                timeout=90,
                headers={
                    "User-Agent":
                        "Mozilla/5.0"
                }
            )

            if response.status_code != 200:

                print(
                    f" Saltada: HTTP "
                    f"{response.status_code}"
                )

                continue

            data = response.content

            # ------------------------------------------------
            # DESCOMPRESIÓN
            # ------------------------------------------------

            if (
                url.lower().endswith(
                    ".gz"
                )
            ):

                try:

                    data = gzip.decompress(
                        data
                    )

                except Exception:

                    print(
                        " No se pudo "
                        "descomprimir como gzip."
                    )

                    continue

            # ------------------------------------------------
            # XML
            # ------------------------------------------------

            root = ET.fromstring(
                data
            )

            # ------------------------------------------------
            # MAPA DE CANALES XML
            # ------------------------------------------------

            xml_channels = {}

            for xml_channel in root.findall(
                "channel"
            ):

                xml_id = (
                    xml_channel.get(
                        "id",
                        ""
                    )
                    or ""
                ).strip()

                if not xml_id:
                    continue

                channel_name = ""

                display_name = (
                    xml_channel.find(
                        "display-name"
                    )
                )

                if (
                    display_name
                    is not None
                ):

                    channel_name = (
                        display_name.text
                        or ""
                    ).strip()

                xml_channels[
                    xml_id
                ] = channel_name

            print(
                f" Canales XML: "
                f"{len(xml_channels)}"
            )

            # ------------------------------------------------
            # BUSCAR PROGRAMAS
            # ------------------------------------------------

            programmes_in_guide = 0

            for programme in root.findall(
                "programme"
            ):

                xml_channel = (
                    programme.get(
                        "channel",
                        ""
                    )
                    or ""
                ).strip()

                if not xml_channel:
                    continue

                # --------------------------------------------
                # BUSCAR LA GUÍA ASOCIADA
                # --------------------------------------------

                matched_guide = None

                for guide in guide_info:

                    guide_site_id = str(
                        guide.get(
                            "site_id",
                            ""
                        )
                        or ""
                    ).strip()

                    guide_channel = str(
                        guide.get(
                            "channel",
                            ""
                        )
                        or ""
                    ).strip()

                    # Caso habitual:
                    # XML channel == site_id
                    if (
                        guide_site_id
                        and
                        xml_channel
                        == guide_site_id
                    ):

                        matched_guide = guide

                        break

                    # Compatibilidad:
                    # XML channel == API channel
                    if (
                        guide_channel
                        and
                        xml_channel
                        == guide_channel
                    ):

                        matched_guide = guide

                        break

                # --------------------------------------------
                # Si no hemos encontrado coincidencia,
                # utilizamos la primera guía asociada.
                # --------------------------------------------

                if (
                    matched_guide
                    is None
                    and guide_info
                ):

                    matched_guide = (
                        guide_info[0]
                    )

                # --------------------------------------------
                # START
                # --------------------------------------------

                start = (
                    programme.get(
                        "start",
                        ""
                    )
                    or ""
                ).strip()

                # --------------------------------------------
                # STOP
                # --------------------------------------------

                stop = (
                    programme.get(
                        "stop",
                        ""
                    )
                    or ""
                ).strip()

                # --------------------------------------------
                # TÍTULO
                # --------------------------------------------

                title_element = (
                    programme.find(
                        "title"
                    )
                )

                title = ""

                if (
                    title_element
                    is not None
                ):

                    title = (
                        title_element.text
                        or ""
                    ).strip()

                if not title:
                    continue

                # --------------------------------------------
                # DESCRIPCIÓN
                # --------------------------------------------

                desc_element = (
                    programme.find(
                        "desc"
                    )
                )

                description = ""

                if (
                    desc_element
                    is not None
                ):

                    description = (
                        desc_element.text
                        or ""
                    ).strip()

                # --------------------------------------------
                # NOMBRE DEL CANAL
                # --------------------------------------------

                channel_name = (
                    xml_channels.get(
                        xml_channel,
                        ""
                    )
                )

                if (
                    not channel_name
                    and matched_guide
                ):

                    channel_name = str(
                        matched_guide.get(
                            "site_name",
                            ""
                        )
                        or ""
                    )

                # --------------------------------------------
                # ID DEL CANAL
                # --------------------------------------------

                api_channel = ""

                if matched_guide:

                    api_channel = str(
                        matched_guide.get(
                            "channel",
                            ""
                        )
                        or ""
                    ).strip()

                # --------------------------------------------
                # FEED
                # --------------------------------------------

                feed = ""

                if matched_guide:

                    feed = str(
                        matched_guide.get(
                            "feed",
                            ""
                        )
                        or ""
                    ).strip()

                # --------------------------------------------
                # DEPORTE
                # --------------------------------------------

                sport_text = (
                    f"{title} "
                    f"{description} "
                    f"{channel_name}"
                )

                sport = detect_sport(
                    sport_text
                )

                # --------------------------------------------
                # GUARDAR PROGRAMA
                # --------------------------------------------

                all_programmes.append({

                    "channel":
                        api_channel,

                    "feed":
                        feed,

                    "epg_channel":
                        xml_channel,

                    "channel_name":
                        channel_name,

                    "start":
                        start,

                    "stop":
                        stop,

                    "title":
                        title,

                    "description":
                        description,

                    "sport":
                        sport,

                    "source":
                        url,
                })

                programmes_in_guide += 1

            print(
                f" Programas obtenidos: "
                f"{programmes_in_guide}"
            )

        except Exception as error:

            print(
                f" Error leyendo EPG: "
                f"{error}"
            )

            continue

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print("")
    print(
        "=========================================="
    )

    print(
        f"Programas EPG obtenidos: "
        f"{len(all_programmes)}"
    )

    print(
        "=========================================="
    )

    return all_programmes


# ============================================================
# COMPATIBILIDAD CON MAIN.PY
# ============================================================

def parse_epg(xml_data):
    """
    Compatibilidad con main.py.

    download_epg() ya devuelve los programas
    preparados.
    """

    return xml_data


# ============================================================
# FILTRAR EVENTOS DEPORTIVOS
# ============================================================

def get_sport_events(programs):
    """
    Devuelve únicamente programas relacionados
    con los cinco deportes configurados.
    """

    events = []

    for program in programs:

        # Si ya tenemos deporte detectado,
        # lo utilizamos directamente.

        sport = program.get(
            "sport"
        )

        if sport in SPORT_KEYWORDS:

            events.append(
                program
            )

            continue

        # ----------------------------------------------------
        # Si no estaba detectado, volvemos a comprobar
        # título + descripción + canal.
        # ----------------------------------------------------

        title = str(
            program.get(
                "title",
                ""
            )
            or ""
        )

        description = str(
            program.get(
                "description",
                ""
            )
            or ""
        )

        channel_name = str(
            program.get(
                "channel_name",
                ""
            )
            or ""
        )

        text = (
            title
            + " "
            + description
            + " "
            + channel_name
        ).lower()

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
    """
    Agrupa los eventos en este orden:

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
    """
    Convierte un evento EPG en una estructura uniforme.
    """

    title = str(
        event.get(
            "title",
            ""
        )
        or ""
    ).strip()

    description = str(
        event.get(
            "description",
            ""
        )
        or ""
    ).strip()

    sport = event.get(
        "sport"
    )

    if not sport:

        sport = detect_sport(
            f"{title} {description}"
        )

    return {

        "id":
            event.get(
                "id"
            ),

        "sport":
            sport,

        "sport_name":
            {
                "football":
                    "FÚTBOL",

                "tennis":
                    "TENIS",

                "basketball":
                    "BALONCESTO",

                "formula1":
                    "FÓRMULA 1",

                "motogp":
                    "MOTOGP",
            }.get(
                sport,
                "OTROS"
            ),

        "title":
            title,

        "description":
            description,

        "channel":
            event.get(
                "channel",
                ""
            ),

        "channel_name":
            event.get(
                "channel_name",
                ""
            ),

        "epg_channel":
            event.get(
                "epg_channel",
                ""
            ),

        "feed":
            event.get(
                "feed",
                ""
            ),

        "start":
            event.get(
                "start",
                ""
            ),

        "stop":
            event.get(
                "stop",
                ""
            ),

        "live":
            bool(
                event.get(
                    "live",
                    False
                )
            ),

        "source":
            event.get(
                "source",
                ""
            ),

        "servers":
            event.get(
                "servers",
                []
            ),
    }


# ============================================================
# EVENTOS EN DIRECTO
# ============================================================

def get_live_events(events):
    """
    Devuelve únicamente los eventos marcados como directos.
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


# ============================================================
# FILTRAR LOS CINCO DEPORTES
# ============================================================

def filter_sports_events(events):
    """
    Conserva únicamente:

    - Fútbol
    - Tenis
    - Baloncesto
    - Fórmula 1
    - MotoGP
    """

    result = []

    for event in events:

        normalized = normalize_event(
            event
        )

        if (
            normalized["sport"]
            in SPORT_KEYWORDS
        ):

            result.append(
                normalized
            )

    return result


# ============================================================
# AÑADIR SERVIDOR
# ============================================================

def add_server(event, server):
    """
    Añade una fuente/servidor a un evento
    sin duplicarlo.
    """

    normalized = normalize_event(
        event
    )

    servers = normalized.get(
        "servers",
        []
    )

    if server not in servers:

        servers.append(
            server
        )

    normalized["servers"] = (
        servers
    )

    return normalized
