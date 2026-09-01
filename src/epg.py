import gzip
import io
import xml.etree.ElementTree as ET

import requests


API_BASE = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API_BASE}/channels.json"
GUIDES_URL = f"{API_BASE}/guides.json"

# Fuente comunitaria adicional actualmente publicada por iptv-org.
# Se utiliza solamente como respaldo.
WORKER_EPG_URL = "https://worker-9dd4.onrender.com/guide.xml.gz"


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
# UTILIDADES
# ============================================================

def clean(value):
    return str(value or "").strip()


def download_json(url, timeout=120):
    response = SESSION.get(
        url,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


def is_http_url(url):
    return (
        isinstance(url, str)
        and (
            url.startswith("http://")
            or url.startswith("https://")
        )
    )


# ============================================================
# CANALES DEPORTIVOS
# ============================================================

def get_sports_channels():

    print()
    print("Descargando canales de iptv-org...")

    channels = download_json(
        CHANNELS_URL
    )

    print(
        f"Canales recibidos: {len(channels)}"
    )

    sports = {}

    for channel in channels:

        if not isinstance(channel, dict):
            continue

        channel_id = clean(
            channel.get("id")
        )

        if not channel_id:
            continue

        categories = channel.get(
            "categories",
            []
        )

        categories = {
            clean(category).lower()
            for category in categories
        }

        if "sports" in categories:

            sports[channel_id] = channel

    print(
        f"Canales deportivos: {len(sports)}"
    )

    return sports


# ============================================================
# GUIDES.JSON
# ============================================================

def get_guide_sources(sports_channels):

    print()
    print("Descargando guides.json...")

    guides = download_json(
        GUIDES_URL
    )

    print(
        f"Entradas de guías recibidas: "
        f"{len(guides)}"
    )

    sources = {}

    sports_ids = set(
        sports_channels.keys()
    )

    for guide in guides:

        if not isinstance(guide, dict):
            continue

        channel_id = clean(
            guide.get("channel")
        )

        if not channel_id:
            continue

        # Solo nos interesan canales deportivos.
        if channel_id not in sports_ids:
            continue

        guide_sources = guide.get(
            "sources",
            []
        )

        if not isinstance(
            guide_sources,
            list
        ):
            continue

        for source in guide_sources:

            if not isinstance(
                source,
                dict
            ):
                continue

            url = clean(
                source.get("url")
            )

            if not is_http_url(url):
                continue

            source_format = clean(
                source.get("format")
            ).upper()

            key = (
                url,
                source_format
            )

            if key not in sources:

                sources[key] = {
                    "url": url,
                    "format": source_format,
                    "channels": set(),
                }

            sources[key][
                "channels"
            ].add(channel_id)

    print(
        f"Fuentes EPG deportivas únicas: "
        f"{len(sources)}"
    )

    return list(
        sources.values()
    )


# ============================================================
# DESCARGAR UNA GUÍA
# ============================================================

def download_guide(source):

    url = source["url"]

    try:

        response = SESSION.get(
            url,
            timeout=60,
        )

        response.raise_for_status()

        data = response.content

        if not data:
            return None

        # GZIP detectado por cabecera.
        if data[:2] == b"\x1f\x8b":

            data = gzip.decompress(
                data
            )

        return data

    except Exception as error:

        print(
            f" ERROR: {url}"
        )

        print(
            f" {error}"
        )

        return None


# ============================================================
# PARSEAR XMLTV
# ============================================================

def parse_xmltv(
    data,
    sports_channels
):

    programs = []

    if not data:
        return programs

    try:

        root = ET.fromstring(
            data
        )

    except Exception as error:

        print(
            f" ERROR XML: {error}"
        )

        return programs

    # --------------------------------------------------------
    # Nombres de canales del XMLTV
    # --------------------------------------------------------

    channel_names = {}

    for channel in root.findall(
        "channel"
    ):

        channel_id = clean(
            channel.get("id")
        )

        if not channel_id:
            continue

        display_name = channel.find(
            "display-name"
        )

        name = ""

        if display_name is not None:
            name = clean(
                display_name.text
            )

        channel_names[
            channel_id
        ] = name

    # --------------------------------------------------------
    # PROGRAMAS
    # --------------------------------------------------------

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

        # Match directo.
        if channel_id not in sports_channels:
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
                ""
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

    return programs


# ============================================================
# RESPALDO: WORKER COMUNITARIO
# ============================================================

def download_worker_epg(
    sports_channels
):

    print()
    print(
        "Intentando fuente EPG comunitaria "
        "de respaldo..."
    )

    print(
        WORKER_EPG_URL
    )

    source = {
        "url": WORKER_EPG_URL,
        "format": "GZIP",
        "channels": set(
            sports_channels.keys()
        ),
    }

    data = download_guide(
        source
    )

    if data is None:

        print(
            "Fuente comunitaria no disponible."
        )

        return []

    programs = parse_xmltv(
        data,
        sports_channels
    )

    print(
        f"Programas encontrados en "
        f"respaldo: {len(programs)}"
    )

    return programs


# ============================================================
# DESCARGA PRINCIPAL
# ============================================================

def download_epg():

    print()
    print(
        "============================================================"
    )
    print(
        "OBTENIENDO PROGRAMACIÓN"
    )
    print(
        "============================================================"
    )

    # --------------------------------------------------------
    # 1. CANALES DEPORTIVOS
    # --------------------------------------------------------

    try:

        sports_channels = (
            get_sports_channels()
        )

    except Exception as error:

        print()
        print(
            "ERROR obteniendo canales:"
        )

        print(error)

        return []

    if not sports_channels:
        return []

    # --------------------------------------------------------
    # 2. FUENTES REALES
    # --------------------------------------------------------

    try:

        sources = get_guide_sources(
            sports_channels
        )

    except Exception as error:

        print()
        print(
            "ERROR obteniendo guides.json:"
        )

        print(error)

        sources = []

    # --------------------------------------------------------
    # 3. DESCARGAR FUENTES
    # --------------------------------------------------------

    all_programs = []

    successful_sources = 0

    failed_sources = 0

    print()

    print(
        "Descargando fuentes EPG reales..."
    )

    print(
        f"Fuentes a comprobar: "
        f"{len(sources)}"
    )

    for index, source in enumerate(
        sources,
        start=1
    ):

        url = source["url"]

        print(
            f"[{index}/{len(sources)}] "
            f"{url}"
        )

        data = download_guide(
            source
        )

        if data is None:

            failed_sources += 1

            continue

        successful_sources += 1

        programs = parse_xmltv(
            data,
            sports_channels
        )

        if programs:

            print(
                f" Programas deportivos: "
                f"{len(programs)}"
            )

            all_programs.extend(
                programs
            )

        else:

            print(
                " Sin programas deportivos "
                "coincidentes."
            )

    # --------------------------------------------------------
    # 4. RESPALDO
    # --------------------------------------------------------

    if not all_programs:

        print()
        print(
            "Las fuentes directas no han "
            "proporcionado programas."
        )

        backup_programs = (
            download_worker_epg(
                sports_channels
            )
        )

        all_programs.extend(
            backup_programs
        )

    # --------------------------------------------------------
    # 5. ELIMINAR DUPLICADOS
    # --------------------------------------------------------

    unique = {}

    for program in all_programs:

        key = (
            program.get("channel", ""),
            program.get("start", ""),
            program.get("stop", ""),
            program.get("title", ""),
        )

        unique[key] = program

    programs = list(
        unique.values()
    )

    # --------------------------------------------------------
    # 6. RESULTADO
    # --------------------------------------------------------

    print()
    print(
        "============================================================"
    )

    print(
        f"Fuentes EPG descargadas correctamente: "
        f"{successful_sources}"
    )

    print(
        f"Fuentes EPG fallidas: "
        f"{failed_sources}"
    )

    print(
        f"Programas EPG deportivos: "
        f"{len(programs)}"
    )

    print(
        "============================================================"
    )

    return programs


# ============================================================
# COMPATIBILIDAD CON MAIN.PY
# ============================================================

def parse_epg(epg_data):

    return epg_data
