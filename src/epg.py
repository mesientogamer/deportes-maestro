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
    Descarga información EPG de canales deportivos.
    """

    print("Descargando información de canales...")

    channels = download_json(
        CHANNELS_URL
    )

    print(
        f"Canales recibidos: {len(channels)}"
    )

    # --------------------------------------------------
    # CANALES DEPORTIVOS
    # --------------------------------------------------

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
            sports_channel_ids.add(
                channel_id
            )

    print(
        f"Canales deportivos: "
        f"{len(sports_channel_ids)}"
    )

    # --------------------------------------------------
    # GUIDES.JSON
    # --------------------------------------------------

    print("Descargando índice de EPG...")

    guides = download_json(
        GUIDES_URL
    )

    print(
        f"Entradas EPG recibidas: "
        f"{len(guides)}"
    )

    # --------------------------------------------------
    # BUSCAR GUIAS QUE TENGAN SOURCES
    # --------------------------------------------------

    print("")
    print("========== GUIAS CON SOURCES ==========")

    count = 0

    for guide in guides:

        if guide.get("sources"):

            print(guide)

            count += 1

            if count >= 10:
                break

    print(
        f"Guias con sources encontradas: {count}"
    )

    print("========================================")
    print("")

    # --------------------------------------------------
    # OBTENER FUENTES EPG DEPORTIVAS
    # --------------------------------------------------

    guide_sources = {}

    for guide in guides:

        channel_id = guide.get(
            "channel"
        )

        if not channel_id:
            continue

        if channel_id not in sports_channel_ids:
            continue

        feed = guide.get(
            "feed"
        )

        site_id = guide.get(
            "site_id",
            ""
        )

        site_name = guide.get(
            "site_name",
            ""
        )

        sources = guide.get(
            "sources",
            []
        )

        for source in sources:

            if isinstance(source, str):

                url = source

            else:

                url = source.get(
                    "url"
                )

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

    # --------------------------------------------------
    # DESCARGAR TODAS LAS FUENTES
    # --------------------------------------------------

    all_programmes = []

    for index, (
        url,
        guide_info
    ) in enumerate(
        guide_sources.items(),
        start=1
    ):

        print(
            f"EPG {index}/"
            f"{len(guide_sources)}: "
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

            # --------------------------------------------------
            # DESCOMPRESIÓN
            # --------------------------------------------------

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

            # --------------------------------------------------
            # LEER XML
            # --------------------------------------------------

            root = ET.fromstring(
                data
            )

            # --------------------------------------------------
            # PROGRAMAS
            # --------------------------------------------------

            for programme in root.findall(
                "programme"
            ):

                xml_channel = (
                    programme.get(
                        "channel",
                        ""
                    )
                )

                if not xml_channel:
                    continue

                start = (
                    programme.get(
                        "start",
                        ""
                    )
                )

                stop = (
                    programme.get(
                        "stop",
                        ""
                    )
                )

                # ------------------------------
                # TÍTULO
                # ------------------------------

                title_element = (
                    programme.find(
                        "title"
                    )
                )

                title = ""

                if title_element is not None:

                    title = (
                        title_element.text
                        or ""
                    ).strip()

                if not title:
                    continue

                # ------------------------------
                # DESCRIPCIÓN
                # ------------------------------

                desc_element = (
                    programme.find(
                        "desc"
                    )
                )

                description = ""

                if desc_element is not None:

                    description = (
                        desc_element.text
                        or ""
                    ).strip()

                # ------------------------------
                # GUÍA ASOCIADA
                # ------------------------------

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

                if matched_guide is None:

                    matched_guide = guide_info[0]

                # ------------------------------
                # GUARDAR PROGRAMA
                # ------------------------------

                all_programmes.append({

                    "channel":
                        matched_guide.get(
                            "channel",
                            ""
                        ),

                    "feed":
                        matched_guide.get(
                            "feed"
                        ),

                    "epg_channel":
                        xml_channel,

                    "channel_name":
                        matched_guide.get(
                            "site_name",
                            ""
                        ),

                    "start":
                        start,

                    "stop":
                        stop,

                    "title":
                        title,

                    "description":
                        description
                    })
