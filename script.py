import json
import requests
from collections import defaultdict

OUTPUT_FILE = "parrilla_deportes_automatica.m3u"

API_BASE = "https://iptv-org.github.io/api"

CHANNELS_URL = f"{API_BASE}/channels.json"
STREAMS_URL = f"{API_BASE}/streams.json"

# EPG pública de IPTV-org.
EPG_URL = "https://iptv-org.github.io/epg/guides/merged.xml.gz"

# ============================================================
# DEPORTES QUE QUEREMOS
# ============================================================

SPORTS = {
    "football": {
        "name": "1. FÚTBOL",
        "keywords": [
            "football",
            "soccer",
            "futbol",
            "fútbol",
            "bein",
            "ssc",
            "alkass",
            "laliga",
            "la liga",
            "champions",
            "uefa",
            "europa league",
        ],
    },

    "tennis": {
        "name": "2. TENIS",
        "keywords": [
            "tennis",
            "tenis",
            "atp",
            "wta",
            "wimbledon",
            "roland garros",
            "french open",
            "us open",
            "australian open",
        ],
    },

    "basketball": {
        "name": "3. BALONCESTO",
        "keywords": [
            "basketball",
            "baloncesto",
            "nba",
            "euroleague",
            "eurocup",
            "fiba",
            "acb",
        ],
    },

    "f1": {
        "name": "4. FÓRMULA 1",
        "keywords": [
            "formula 1",
            "formula1",
            "f1",
        ],
    },

    "motogp": {
        "name": "5. MOTOGP",
        "keywords": [
            "motogp",
            "moto gp",
            "motorcycle gp",
        ],
    },
}


# ============================================================
# IDIOMAS
# ============================================================
#
# NO hacemos una lista cerrada.
# El script utiliza todos los idiomas que IPTV-org tenga
# asociados a los canales/feeds deportivos.
#
# Así, si mañana aparece un idioma nuevo, no hay que cambiar
# el código.
# ============================================================


def download_json(url):
    print(f"Descargando: {url}")

    response = requests.get(
        url,
        timeout=90,
        headers={
            "User-Agent": "Mozilla/5.0"
        },
    )

    response.raise_for_status()

    return response.json()


def normalize(text):
    if not text:
        return ""

    return str(text).lower().strip()


def channel_text(channel):
    """
    Construye un texto con toda la información útil
    del canal para detectar el deporte.
    """

    values = []

    values.append(channel.get("name", ""))

    for name in channel.get("alt_names", []):
        values.append(name)

    for category in channel.get("categories", []):
        values.append(category)

    return " ".join(
        normalize(value)
        for value in values
        if value
    )


def detect_sport(channel):
    """
    Detecta el deporte utilizando nombre,
    nombres alternativos y categorías.
    """

    text = channel_text(channel)

    # Primero usamos las categorías oficiales.
    categories = {
        normalize(category)
        for category in channel.get(
            "categories",
            []
        )
    }

    if "sports" not in categories:
        return None

    # Fútbol
    for keyword in SPORTS["football"]["keywords"]:
        if keyword in text:
            return "football"

    # Tenis
    for keyword in SPORTS["tennis"]["keywords"]:
        if keyword in text:
            return "tennis"

    # Baloncesto
    for keyword in SPORTS["basketball"]["keywords"]:
        if keyword in text:
            return "basketball"

    # Fórmula 1
    for keyword in SPORTS["f1"]["keywords"]:
        if keyword in text:
            return "f1"

    # MotoGP
    for keyword in SPORTS["motogp"]["keywords"]:
        if keyword in text:
            return "motogp"

    return None


def get_languages(channel):
    """
    IPTV-org actualmente mantiene los idiomas a nivel
    de feed, por lo que este campo puede no existir
    directamente en channels.json.

    Si existe, lo aprovechamos.
    """

    languages = channel.get(
        "languages",
        []
    )

    if isinstance(languages, list):
        return [
            str(language)
            for language in languages
            if language
        ]

    return []


def stream_is_usable(stream):
    """
    Descarta entradas claramente inválidas.
    """

    url = stream.get("url")

    if not url:
        return False

    if not (
        url.startswith("http://")
        or url.startswith("https://")
    ):
        return False

    label = normalize(
        stream.get("label", "")
    )

    # No incluimos streams que IPTV-org
    # marque explícitamente como geo-blocked.
    if "geo-blocked" in label:
        return False

    return True


def stream_quality(stream):
    quality = stream.get(
        "quality",
        ""
    )

    if quality:
        return str(quality)

    return ""


def main():

    print("=" * 60)
    print("ACTUALIZADOR DE PARRILLA DEPORTIVA")
    print("=" * 60)

    # --------------------------------------------------------
    # Descargar datos
    # --------------------------------------------------------

    channels = download_json(
        CHANNELS_URL
    )

    streams = download_json(
        STREAMS_URL
    )

    print()
    print(
        f"Canales recibidos: {len(channels)}"
    )

    print(
        f"Streams recibidos: {len(streams)}"
    )

    # --------------------------------------------------------
    # Indexar streams por canal
    # --------------------------------------------------------

    streams_by_channel = defaultdict(list)

    for stream in streams:

        channel_id = stream.get(
            "channel"
        )

        if not channel_id:
            continue

        if not stream_is_usable(
            stream
        ):
            continue

        streams_by_channel[
            channel_id
        ].append(stream)

    # --------------------------------------------------------
    # Crear grupos deportivos
    # --------------------------------------------------------

    groups = {
        sport: []
        for sport in SPORTS
    }

    seen_urls = set()

    # --------------------------------------------------------
    # Procesar canales
    # --------------------------------------------------------

    for channel in channels:

        channel_id = channel.get(
            "id"
        )

        if not channel_id:
            continue

        sport = detect_sport(
            channel
        )

        if sport is None:
            continue

        channel_streams = (
            streams_by_channel.get(
                channel_id,
                []
            )
        )

        if not channel_streams:
            continue

        channel_name = channel.get(
            "name",
            channel_id
        )

        languages = get_languages(
            channel
        )

        for stream in channel_streams:

            url = stream.get(
                "url"
            )

            if not url:
                continue

            # Evitar duplicados.
            if url in seen_urls:
                continue

            seen_urls.add(url)

            title = stream.get(
                "title",
                ""
            )

            quality = stream_quality(
                stream
            )

            groups[sport].append({
                "id": channel_id,
                "name": channel_name,
                "url": url,
                "title": title,
                "quality": quality,
                "languages": languages,
            })

    # --------------------------------------------------------
    # Construir M3U
    # --------------------------------------------------------

    output = [
        "#EXTM3U",
        f'#EXT-X-EPG-URL="{EPG_URL}"',
        "",
    ]

    total = 0

    for sport_id in SPORTS:

        sport_name = SPORTS[
            sport_id
        ]["name"]

        entries = groups[
            sport_id
        ]

        # Orden alfabético por canal.
        entries.sort(
            key=lambda item: (
                normalize(
                    item["name"]
                ),
                normalize(
                    item["quality"]
                ),
            )
        )

        output.append(
            f"# ===== {sport_name} ====="
        )

        print()
        print(
            f"{sport_name}: "
            f"{len(entries)} streams"
        )

        for entry in entries:

            channel_id = entry["id"]

            channel_name = entry[
                "name"
            ]

            display_name = channel_name

            if entry["title"]:
                if entry["title"] != channel_name:
                    display_name += (
                        f" - {entry['title']}"
                    )

            if entry["quality"]:
                display_name += (
                    f" [{entry['quality']}]"
                )

            # ------------------------------------------------
            # tvg-id es lo importante para relacionar el canal
            # con la EPG.
            # ------------------------------------------------

            output.append(
                f'#EXTINF:-1 '
                f'tvg-id="{channel_id}" '
                f'group-title="{sport_name}",'
                f'{display_name}'
            )

            output.append(
                entry["url"]
            )

            total += 1

        output.append("")

    # --------------------------------------------------------
    # Guardar archivo
    # --------------------------------------------------------

    result = "\n".join(
        output
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:

        file.write(result)

    print()
    print("=" * 60)
    print(
        f"TOTAL DE STREAMS: {total}"
    )
    print(
        f"ARCHIVO: {OUTPUT_FILE}"
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
