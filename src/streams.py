import requests


STREAMS_URL = "https://iptv-org.github.io/api/streams.json"


def download_streams():
    """
    Descarga la base de datos pública de streams.
    """

    response = requests.get(
        STREAMS_URL,
        timeout=120,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    return response.json()


def group_streams_by_channel(streams):
    """
    Agrupa los streams utilizando el ID del canal.
    """

    grouped = {}

    for stream in streams:

        channel_id = stream.get(
            "channel"
        )

        url = stream.get(
            "url"
        )

        if not channel_id or not url:
            continue

        if not (
            url.startswith("http://")
            or url.startswith("https://")
        ):
            continue

        grouped.setdefault(
            channel_id,
            []
        ).append(stream)

    return grouped


def get_streams_for_channel(
    grouped_streams,
    channel_id
):
    """
    Devuelve todos los streams disponibles
    para un canal concreto.
    """

    return grouped_streams.get(
        channel_id,
        []
    )


def remove_duplicate_streams(streams):
    """
    Elimina URLs repetidas.
    """

    result = []
    seen = set()

    for stream in streams:

        url = stream.get(
            "url"
        )

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        result.append(stream)

    return result
