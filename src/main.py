from pathlib import Path
import sys
import json
from datetime import datetime, timezone, timedelta

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
    if not CONFIG_FILE.exists():
        print("No se encontró config/config.json.")
        return {}

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_xmltv_time(value):
    """
    Convierte una fecha XMLTV como:
    20260902183000 +0000

    a datetime UTC.
    """
    text = str(value or "").strip()

    if not text:
        return None

    parts = text.split()

    if not parts:
        return None

    base = parts[0]

    try:
        dt = datetime.strptime(
            base,
            "%Y%m%d%H%M%S"
        )
    except ValueError:
        return None

    if len(parts) > 1:
        tz_text = parts[1].strip()

        if (
            len(tz_text) == 5
            and tz_text[0] in "+-"
            and tz_text[1:].isdigit()
        ):
            sign = (
                1
                if tz_text[0] == "+"
                else -1
            )

            hours = int(tz_text[1:3])
            minutes = int(tz_text[3:5])

            offset = timedelta(
                hours=hours,
                minutes=minutes
            )

            if sign == -1:
                offset = -offset

            dt = dt.replace(
                tzinfo=timezone(offset)
            )
        else:
            dt = dt.replace(
                tzinfo=timezone.utc
            )
    else:
        dt = dt.replace(
            tzinfo=timezone.utc
        )

    return dt.astimezone(timezone.utc)


def is_live_now(program):
    """
    Comprueba si el programa está ocurriendo
    exactamente en este momento.
    """

    start = parse_xmltv_time(
        program.get("start")
    )

    stop = parse_xmltv_time(
        program.get("stop")
    )

    if start is None or stop is None:
        return False

    now = datetime.now(timezone.utc)

    return start <= now < stop


def create_events(programs, streams_by_channel):

    events = []

    total_programs = 0
    skipped_not_live = 0
    skipped_no_stream = 0

    for program in programs:

        total_programs += 1

        # =========================================================
        # SOLO PROGRAMAS QUE ESTÁN EN DIRECTO AHORA
        # =========================================================

        if not is_live_now(program):
            skipped_not_live += 1
            continue

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

        channel_id = str(
            program.get(
                "channel",
                ""
            )
        ).strip()

        if not title or not channel_id:
            continue

        sport = program.get("sport")

        if not sport:
            sport = detect_sport(
                title,
                description
            )

        if sport is None:
            continue

        channel_streams = streams_by_channel.get(
            channel_id,
            []
        )

        if not channel_streams:
            skipped_no_stream += 1
            continue

        servers = []

        for stream in channel_streams:

            url = stream.get("url")

            if not url:
                continue

            servers.append(
                {
                    "url": url,
                    "name": stream.get(
                        "title",
                        "Fuente"
                    ),
                }
            )

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

            "channel_name": program.get(
                "channel_name",
                ""
            ),

            "epg_channel": program.get(
                "epg_channel",
                ""
            ),

            "feed": program.get(
                "feed",
                ""
            ),

            "start": program.get(
                "start",
                ""
            ),

            "stop": program.get(
                "stop",
                ""
            ),

            # IMPORTANTE:
            # Solo llegamos aquí si está en directo.
            "live": True,

            "servers": servers,
        }

        events.append(
            normalize_event(event)
        )

    print()
    print("CONTROL DE DIRECTOS")
    print(
        f"Programas revisados: "
        f"{total_programs}"
    )
    print(
        f"Programas descartados por "
        f"no estar en directo: "
        f"{skipped_not_live}"
    )
    print(
        f"Programas sin fuente: "
        f"{skipped_no_stream}"
    )
    print(
        f"Eventos LIVE encontrados: "
        f"{len(events)}"
    )

    return events


def main():

    print("=" * 60)
    print("DEPORTES MAESTRO")
    print("=" * 60)

    config = load_config()

    print()
    print("Deportes configurados:")

    for sport in config.get(
        "sports",
        []
    ):
        print(f" - {sport}")

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

    print()

    print(
        "3/3 - Relacionando eventos LIVE "
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

    print()

    total_events = 0

    for sport, sport_events in grouped.items():

        print(
            f"{sport}: "
            f"{len(sport_events)} eventos LIVE"
        )

        total_events += len(
            sport_events
        )

    print()

    print(
        f"TOTAL EVENTOS LIVE: "
        f"{total_events}"
    )

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
