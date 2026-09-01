from pathlib import Path
import sys
import json

SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from epg import download_epg, parse_epg
from streams import (
    download_streams,
    group_streams_by_channel,
    remove_duplicate_streams,
)
from events import (
    detect_sport,
    normalize_event,
    filter_sports_events,
    group_events_by_sport,
)
from m3u import save_m3u


CONFIG_FILE = (
    SRC_DIR.parent
    / "config"
    / "config.json"
)


def load_config():
    """Carga la configuración del proyecto."""

    if not CONFIG_FILE.exists():
        print(
            "No se encontró config/config.json."
        )

        return {}

    with open(
        CONFIG_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def create_events(programs, streams_by_channel):
    """
    Relaciona los programas de la EPG con los streams
    disponibles para cada canal.

    Cada programa puede tener varias fuentes.
    """

    events = []

    for program in programs:

        title = str(
            program.get(
                "title",
                ""
            )
        ).strip()

        description = str(
            program.get(
                "description",
                ""
            )
        ).strip()

        channel_id = program.get(
            "channel",
            ""
        )

        if not title or not channel_id:
            continue

        sport = detect_sport(
            title,
            description
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

        servers = []

        for stream in channel_streams:

            url = stream.get(
                "url"
            )

            if not url:
                continue

            servers.append({
                "url": url,
                "name": stream.get(
                    "title",
                    "Fuente"
                ),
            })

        servers = remove_duplicate_streams(
            servers
        )

        if not servers:
            continue

        event = {
            "id": (
                f"{channel_id}_"
                f"{program.get('start', '')}_"
                f"{title}"
            ),
            "sport": sport,
            "title": title,
            "description": description,
            "channel": channel_id,
            "start": program.get(
                "start",
                ""
            ),
            "stop": program.get(
                "stop",
                ""
            ),
            "live": True,
            "servers": servers,
        }

        events.append(
            normalize_event(event)
        )

    return events


def main():

    print("=" * 60)
    print("DEPORTES MAESTRO")
    print("=" * 60)

    config = load_config()

    print()
    print(
        "Deportes configurados:"
    )

    for sport in config.get(
        "sports",
        []
    ):
        print(
            f" - {sport}"
        )

    # ------------------------------------------------------
    # 1. EPG
    # ------------------------------------------------------

    print()
    print(
        "1/3 - Obteniendo programación..."
    )

    epg_data = download_epg()

    programs = parse_epg(
        epg_data
    )

    print(
        f"Programas obtenidos: "
        f"{len(programs)}"
    )

    # ------------------------------------------------------
    # 2. STREAMS
    # ------------------------------------------------------

    print()
    print(
        "2/3 - Obteniendo fuentes..."
    )

    streams = download_streams()

    print(
        f"Streams recibidos: "
        f"{len(streams)}"
    )

    streams_by_channel = (
        group_streams_by_channel(
            streams
        )
    )

    # ------------------------------------------------------
    # 3. EVENTOS
    # ------------------------------------------------------

    print()
    print(
        "3/3 - Relacionando eventos "
        "con fuentes..."
    )

    events = create_events(
        programs,
        streams_by_channel
    )

    events = filter_sports_events(
        events
    )

    grouped = group_events_by_sport(
        events
    )

    # ------------------------------------------------------
    # Mostrar resultados
    # ------------------------------------------------------

    print()

    total_events = 0

    for sport, sport_events in grouped.items():

        print(
            f"{sport}: "
            f"{len(sport_events)} eventos"
        )

        total_events += len(
            sport_events
        )

    print()
    print(
        f"TOTAL EVENTOS: "
        f"{total_events}"
    )

    # ------------------------------------------------------
    # Generar M3U
    # ------------------------------------------------------

    print()
    print(
        "Generando parrilla..."
    )

    output_file = save_m3u(
        events
    )

    print(
        f"Parrilla creada en: "
        f"{output_file}"
    )

    print()
    print("=" * 60)
    print("PROCESO FINALIZADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
