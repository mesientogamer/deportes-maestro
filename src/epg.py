import gzip
import io
import xml.etree.ElementTree as ET

import requests


# ============================================================
# CONFIGURACIÓN
# ============================================================

API_BASE = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API_BASE}/channels.json"
GUIDES_URL = f"{API_BASE}/guides.json"

EPG_BASE = "https://iptv-org.github.io/epg/guides"


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
    ],

    "formula1": [
        "formula 1",
        "formula1",
        "f1",
        "grand prix",
        "grand prix",
        "gp ",
        "formula one",
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
        )
    }
)


# ============================================================
# DESCARGA JSON
# ============================================================

def download_json(url):
    response = SESSION.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DETECCIÓN DE DEPORTE
# ============================================================

def detect_sport(text):

    text = str(text or "").lower()

    for sport, keywords in SPORT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                return sport

    return None


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def clean_text(value):

    return str(value or "").strip()


# ============================================================
# OBTENER URLs EPG DE UNA GUÍA
# ============================================================

def get_guide_urls(guide):

    urls = []

    if not isinstance(guide, dict):
        return urls

    # --------------------------------------------------------
    # FORMATO ANTIGUO / DIRECTO
    # --------------------------------------------------------

    direct_url = guide.get("url")

    if direct_url:

        direct_url = clean_text(direct_url)

        if direct_url:
            urls.append(direct_url)

    # --------------------------------------------------------
    # FORMATO ACTUAL: sources[]
    # --------------------------------------------------------

    sources = guide.get("sources", [])

    if isinstance(sources, list):

        for source in sources:

            if not isinstance(source, dict):
                continue

            source_url = source.get("url")

            if source_url:

                source_url = clean_text(source_url)

                if source_url:
                    urls.append(source_url)

    # --------------------------------------------------------
    # ELIMINAR DUPLICADOS
    # --------------------------------------------------------

    result = []

    seen = set()

    for url in urls:

        if url in seen:
            continue

        seen.add(url)
        result.append(url)

    return result


# ============================================================
# CREAR URL EPG PÚBLICA DE IPTVO-RG
# ============================================================

def build_public_epg_urls(guide):

    urls = []

    if not isinstance(guide, dict):
        return urls

    site = clean_text(
        guide.get("site")
    )

    lang = clean_text(
        guide.get("lang")
    )

    if not site or not lang:
        return urls

    # --------------------------------------------------------
    # GUÍA XML NORMAL
    # --------------------------------------------------------

    urls.append(
        f"{EPG_BASE}/{lang}/{site}.xml"
    )

    # --------------------------------------------------------
    # GUÍA GZIP
    # --------------------------------------------------------

    urls.append(
        f"{EPG_BASE}/{lang}/{site}.xml.gz"
    )

    return urls


# ============================================================
# OBTENER TODAS LAS POSIBLES URLs
# ============================================================

def collect_guide_urls(guide):

    urls = []

    # URLs declaradas por la API
    urls.extend(
        get_guide_urls(guide)
    )

    # URLs públicas estándar de iptv-org/epg
    urls.extend(
        build_public_epg_urls(guide)
    )

    # --------------------------------------------------------
    # DEDUPLICAR
    # --------------------------------------------------------

    result = []

    seen = set()

    for url in urls:

        if not url:
            continue

        url = clean_text(url)

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)

        result.append(url)

    return result


# ============================================================
# DESCARGAR XML EPG
# ============================================================

def download_xml(url):

    response = SESSION.get(
        url,
        timeout=45,
    )

    if response.status_code != 200:

        return None

    data = response.content

    if not data:
        return None

    # --------------------------------------------------------
    # DETECTAR GZIP POR EXTENSIÓN
    # --------------------------------------------------------

    if url.lower().endswith(".gz"):

        try:

            data = gzip.decompress(
                data
            )

        except Exception:

            return None

    else:

        # ----------------------------------------------------
        # DETECTAR GZIP POR LOS BYTES
        # ----------------------------------------------------

        if data[:2] == b"\x1f\x8b":

            try:

                data = gzip.decompress(
                    data
                )

            except Exception:

                return None

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

    except Exception:

        return None


# ============================================================
# CREAR MAPA DE CANALES XML
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
# BUSCAR GUÍA QUE CORRESPONDE A UN CANAL XML
# ============================================================

def match_guide(
    xml_channel,
    guide_info
):

    for guide in guide_info:

        if not isinstance(
            guide,
            dict
        ):
            continue

        site_id = clean_text(
            guide.get(
                "site_id",
                ""
            )
        )

        channel_id = clean_text(
            guide.get(
                "channel",
                ""
            )
        )

        # Caso habitual:
        # XML channel == site_id
        if (
            site_id
            and
            xml_channel == site_id
        ):

            return guide

        # Compatibilidad:
        # XML channel == API channel
        if (
            channel_id
            and
            xml_channel == channel_id
        ):

            return guide

    # --------------------------------------------------------
    # Si solo hay una guía asociada, usarla
    # --------------------------------------------------------

    if len(guide_info) == 1:

        return guide_info[0]

    return None


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
# DESCARGA EPG PRINCIPAL
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

    # ========================================================
    # 1. CANALES
    # ========================================================

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

    # ========================================================
    # 2. CANALES DEPORTIVOS
    # ========================================================

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
            clean_text(category).lower()
            for category in categories
        }

        if (
            "sports"
            in
            categories_normalized
        ):

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

    # ========================================================
    # 3. GUÍAS
    # ========================================================

    print("")
    print(
        "Descargando índice de EPG..."
    )

    guides = download_json(
        GUIDES_URL
    )

    print(
        f"Entradas EPG recibidas: "
        f"{len(guides)}"
    )

    # ========================================================
    # DEBUG
    # ========================================================

    print("")
    print(
        "========== PRIMERAS GUÍAS =========="
    )

    for guide in guides[:10]:

        print(
            guide
        )

    print(
        "===================================="
    )
    print("")

    # ========================================================
    # 4. CREAR MAPA DE GUÍAS
    # ========================================================

    guide_map = {}

    guides_without_direct_url = 0

    guides_with_fallback = 0

    for guide in guides:

        if not isinstance(
            guide,
            dict
        ):
            continue

        channel_id = clean_text(
            guide.get(
                "channel",
                ""
            )
        )

        # ----------------------------------------------------
        # SI LA GUÍA TIENE CANAL, FILTRAR POR DEPORTIVO
        # ----------------------------------------------------

        if (
            channel_id
            and
            channel_id not in sports_channels
        ):

            continue

        direct_urls = get_guide_urls(
            guide
        )

        if not direct_urls:

            guides_without_direct_url += 1

        # ----------------------------------------------------
        # TODAS LAS POSIBLES URL
        # ----------------------------------------------------

        urls = collect_guide_urls(
            guide
        )

        if not urls:
            continue

        if not direct_urls:

            guides_with_fallback += 1

        # ----------------------------------------------------
        # GUARDAR CADA URL
        # ----------------------------------------------------

        for url in urls:

            if url not in guide_map:

                guide_map[
                    url
                ] = []

            guide_map[
                url
            ].append(
                guide
            )

    print(
        f"Guías deportivas sin URL directa: "
        f"{guides_without_direct_url}"
    )

    print(
        f"Guías a las que se aplicó URL pública alternativa: "
        f"{guides_with_fallback}"
    )

    print(
        f"Fuentes EPG deportivas únicas: "
        f"{len(guide_map)}"
    )

    # ========================================================
    # 5. SI NO HAY GUÍAS
    # ========================================================

    if not guide_map:

        print("")
        print(
            "ATENCIÓN: no se encontraron "
            "fuentes EPG."
        )

        print(
            "Se devolverán 0 programas."
        )

        return []

    # ========================================================
    # 6. DESCARGAR GUÍAS
    # ========================================================

    all_programmes = []

    total_guides = len(
        guide_map
    )

    successful_guides = 0

    failed_guides = 0

    # --------------------------------------------------------
    # IMPORTANTE:
    # No ponemos límite artificial al número de fuentes.
    # --------------------------------------------------------

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

        data = download_xml(
            url
        )

        if data is None:

            print(
                " Saltada: no se pudo descargar."
            )

            failed_guides += 1

            continue

        root = parse_xml(
            data
        )

        if root is None:

            print(
                " Saltada: XML inválido."
            )

            failed_guides += 1

            continue

        successful_guides += 1

        # ----------------------------------------------------
        # MAPA DE CANALES
        # ----------------------------------------------------

        xml_channels = (
            build_xml_channel_map(
                root
            )
        )

        print(
            f" Canales XML: "
            f"{len(xml_channels)}"
        )

        programmes_in_guide = 0

        # ----------------------------------------------------
        # PROGRAMAS
        # ----------------------------------------------------

        for programme in root.findall(
            "programme"
        ):

            xml_channel = clean_text(
                programme.get(
                    "channel",
                    ""
                )
            )

            if not xml_channel:
                continue

            # ------------------------------------------------
            # GUÍA CORRESPONDIENTE
            # ------------------------------------------------

            matched_guide = match_guide(
                xml_channel,
                guide_info
            )

            # ------------------------------------------------
            # START
            # ------------------------------------------------

            start = clean_text(
                programme.get(
                    "start",
                    ""
                )
            )

            # ------------------------------------------------
            # STOP
            # ------------------------------------------------

            stop = clean_text(
                programme.get(
                    "stop",
                    ""
                )
            )

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title = get_xml_text(
                programme,
                "title"
            )

            if not title:
                continue

            # ------------------------------------------------
            # DESCRIPTION
            # ------------------------------------------------

            description = get_xml_text(
                programme,
                "desc"
            )

            # ------------------------------------------------
            # CANAL
            # ------------------------------------------------

            channel_name = (
                xml_channels.get(
                    xml_channel,
                    ""
                )
            )

            # ------------------------------------------------
            # DATOS DE LA GUÍA
            # ------------------------------------------------

            api_channel = ""

            feed = ""

            site_name = ""

            site = ""

            lang = ""

            if matched_guide:

                api_channel = clean_text(
                    matched_guide.get(
                        "channel",
                        ""
                    )
                )

                feed = clean_text(
                    matched_guide.get(
                        "feed",
                        ""
                    )
                )

                site_name = clean_text(
                    matched_guide.get(
                        "site_name",
                        ""
                    )
                )

                site = clean_text(
                    matched_guide.get(
                        "site",
                        ""
                    )
                )

                lang = clean_text(
                    matched_guide.get(
                        "lang",
                        ""
                    )
                )

            if not channel_name:

                channel_name = (
                    site_name
                    or
                    xml_channel
                )

            # ------------------------------------------------
            # DEPORTE
            # ------------------------------------------------

            sport_text = (
                f"{title} "
                f"{description} "
                f"{channel_name}"
            )

            sport = detect_sport(
                sport_text
            )

            # ------------------------------------------------
            # SI EL CANAL ES DEPORTIVO PERO EL TÍTULO
            # NO CONTIENE EL DEPORTE, BUSCAR POR NOMBRE
            # ------------------------------------------------

            if not sport:

                channel_lower = (
                    channel_name.lower()
                )

                sport = detect_sport(
                    channel_lower
                )

            # ------------------------------------------------
            # GUARDAR
            # ------------------------------------------------

            all_programmes.append(
                {
                    "channel": api_channel,
                    "feed": feed,
                    "epg_channel": xml_channel,
                    "channel_name": channel_name,
                    "start": start,
                    "stop": stop,
                    "title": title,
                    "description": description,
                    "sport": sport,
                    "source": url,
                    "site": site,
                    "lang": lang,
                    "live": False,
                    "servers": [],
                }
            )

            programmes_in_guide += 1

        print(
            f" Programas obtenidos: "
            f"{programmes_in_guide}"
        )

    # ========================================================
    # RESULTADO
    # ========================================================

    print("")
    print(
        "=========================================="
    )

    print(
        f"Fuentes EPG descargadas correctamente: "
        f"{successful_guides}"
    )

    print(
        f"Fuentes EPG fallidas: "
        f"{failed_guides}"
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

    sport_names = {
        "football": "FÚTBOL",
        "tennis": "TENIS",
        "basketball": "BALONCESTO",
        "formula1": "FÓRMULA 1",
        "motogp": "MOTOGP",
    }

    return {
        "id": event.get(
            "id"
        ),

        "sport": sport,

        "sport_name": sport_names.get(
            sport,
            "OTROS"
        ),

        "title": title,

        "description": description,

        "channel": event.get(
            "channel",
            ""
        ),

        "channel_name": event.get(
            "channel_name",
            ""
        ),

        "epg_channel": event.get(
            "epg_channel",
            ""
        ),

        "feed": event.get(
            "feed",
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
            event.get(
                "live",
                False
            )
        ),

        "source": event.get(
            "source",
            ""
        ),

        "servers": event.get(
            "servers",
            []
        ),
    }


# ============================================================
# EVENTOS EN DIRECTO
# ============================================================

def get_live_events(events):

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

def add_server(
    event,
    server
):

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

    normalized[
        "servers"
    ] = servers

    return normalized
