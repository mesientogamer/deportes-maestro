import requests

# Base de datos global de canales abiertos
URL_MUNDIAL = "https://github.io"

# Idiomas estables inmunes a bloqueos en España
IDIOMAS_INMUNES = ["lang=\"ara\"", "lang=\"fas\"", "lang=\"tur\"", "lang=\"rus\"", "lang=\"vie\"", "-ara", "-tur", "arabic"]

# Palabras clave por deporte
KW_MOTOR = ["f1", "formula 1", "motogp", "moto gp", "racing", "servustv", "orfsport"]
KW_FUTBOL = ["futbol", "football", "soccer", "match", "kick", "ssc", "alkass", "bein", "laliga", "champions"]
KW_TENIS = ["tennis", "tenis", "atp", "wta", "wimbledon", "alcaraz", "sinner", "djokovic", "open"]
KW_BASKET = ["basket", "basketball", "nba", "acb", "euroleague"]
KW_COMBATE = ["mma", "ufc", "boxeo", "boxing", "wwe"]
KW_BALONMANO = ["balonmano", "handball", "ehf"]

m3u_final = "#EXTM3U\n"

try:
    respuesta = requests.get(URL_MUNDIAL, timeout=25)
    if respuesta.status_code == 200:
        lineas = respuesta.text.splitlines()
        metadata = ""
        
        for linea in lineas:
            if linea.startswith("#EXTINF"):
                metadata = linea
            elif linea.startswith("http") and metadata != "":
                meta_low = metadata.lower()
                
                # Filtro de idioma anti-bloqueo
                if any(lang in metadata for lang in IDIOMAS_INMUNES) or "arabic" in meta_low:
                    # Clasificación directa según tu orden de deportes preferido
                    if any(kw in meta_low for kw in KW_MOTOR):
                        m3u_final += f'#EXTINF:-1 group-title="1. MOTOR (F1 / MotoGP)",Canal Motor\n{linea}\n'
                    elif any(kw in meta_low for kw in KW_FUTBOL):
                        m3u_final += f'#EXTINF:-1 group-title="2. FÚTBOL MUNDIAL",Canal Futbol\n{linea}\n'
                    elif any(kw in meta_low for kw in KW_TENIS):
                        m3u_final += f'#EXTINF:-1 group-title="3. TENIS (Alcaraz/ATP/WTA)",Canal Tenis\n{linea}\n'
                    elif any(kw in meta_low for kw in KW_BASKET):
                        m3u_final += f'#EXTINF:-1 group-title="4. BALONCESTO MUNDIAL",Canal Baloncesto\n{linea}\n'
                    elif any(kw in meta_low for kw in KW_COMBATE):
                        m3u_final += f'#EXTINF:-1 group-title="5. MMA Y COMBATE",Canal Combate\n{linea}\n'
                    elif any(kw in meta_low for kw in KW_BALONMANO):
                        m3u_final += f'#EXTINF:-1 group-title="6. BALONMANO",Canal Balonmano\n{linea}\n'
                metadata = ""
except Exception:
    pass

# Escribir el archivo final de forma directa
with open("parrilla_deportes_automatica.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_final)
