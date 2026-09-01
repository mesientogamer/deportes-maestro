import requests

# Base de datos global de canales abiertos de todo el mundo
URL_MUNDIAL = "https://github.io"

# Idiomas de países lejanos + Árabe (Inmunes a los bloqueos de Movistar/Vodafone en España)
IDIOMAS_INMUNES = ["lang=\"ara\"", "lang=\"fas\"", "lang=\"tur\"", "lang=\"rus\"", "lang=\"vie\"", "-ara", "-tur", "arabic"]

# Palabras clave avanzadas para capturar los deportes ordenados
KW_MOTOR = ["f1", "formula 1", "motogp", "moto gp", "racing", "servustv", "orfsport"]
KW_FUTBOL = ["futbol", "football", "soccer", "match", "kick", "ssc", "alkass", "bein", "laliga", "champions"]
KW_TENIS = ["tennis", "tenis", "atp", "wta", "wimbledon", "alcaraz", "sinner", "djokovic", "open"]
KW_BASKET = ["basket", "basketball", "nba", "acb", "euroleague"]
KW_COMBATE = ["mma", "ufc", "boxeo", "boxing", "wwe"]
KW_BALONMANO = ["balonmano", "handball", "ehf"]

canales_motor = []
canales_futbol = []
canales_tenis = []
canales_basket = []
canales_combate = []
canales_balonmano = []

try:
    respuesta = requests.get(URL_MUNDIAL, timeout=25)
    if respuesta.status_code == 200:
        lineas = respuesta.text.splitlines()
        metadata = None
        
        for linea in lineas:
            if linea.startswith("#EXTINF"):
                metadata = linea
            elif linea.startswith("http") and metadata:
                meta_low = metadata.lower()
                
                # Filtro estricto: Solo canales en árabe o idiomas estratégicos internacionales
                if any(lang in metadata for lang in IDIOMAS_INMUNES) or "arabic" in meta_low:
                    
                    # Clasificación por el orden de prioridad que elegiste
                    if any(kw in meta_low for kw in KW_MOTOR):
                        canales_motor.append((metadata, linea))
                    elif any(kw in meta_low for kw in KW_FUTBOL):
                        canales_futbol.append((metadata, linea))
                    elif any(kw in meta_low for kw in KW_TENIS):
                        canales_tenis.append((metadata, linea))
                    elif any(kw in meta_low for kw in KW_BASKET):
                        canales_basket.append((metadata, linea))
                    elif any(kw in meta_low for kw in KW_COMBATE):
                        canales_combate.append((metadata, linea))
                    elif any(kw in meta_low for kw in KW_BALONMANO):
                        canales_balonmano.append((metadata, linea))
                metadata = None
except Exception:
    pass

# Construcción de la lista para Drama Live respetando tu orden de categorías estricto
m3u_final = "#EXTM3U\n"

# 1. MOTOR (F1 / MotoGP)
for meta, link in canales_motor:
    nombre_canal = meta.split(",")[-1] if "," in meta else "Canal Motor"
    m3u_final += f'#EXTINF:-1 group-title="1. MOTOR (F1 / MotoGP)",{nombre_canal}\n{link}\n'

# 2. FÚTBOL MUNDIAL
for meta, link in canales_futbol:
    nombre_canal = meta.split(",")[-1] if "," in meta else "Canal Futbol"
    m3u_final += f'#EXTINF:-1 group-title="2. FÚTBOL MUNDIAL",{nombre_canal}\n{link}\n'

# 3. TENIS INTERNACIONAL (Alcaraz / ATP / WTA)
for meta, link in canales_tenis:
    nombre_canal = meta.split(",")[-1] if "," in meta else "Canal Tenis"
    m3u_final += f'#EXTINF:-1 group-title="3. TENIS (Alcaraz/ATP/WTA)",{nombre_canal}\n{link}\n'

# 4. BALONCESTO TOTAL
for meta, link in canales_basket:
    nombre_canal = meta.split(",")[-1] if "," in meta else "Canal Baloncesto"
    m3u_final += f'#EXTINF:-1 group-title="4. BALONCESTO MUNDIAL",{nombre_canal}\n{link}\n'

# 5. MMA Y COMBATE
for meta, link in canales_combate:
    nombre_canal = meta.split(",")[-1] if "," in meta else "Canal Combate"
    m3u_final += f'#EXTINF:-1 group-title="5. MMA Y COMBATE",{nombre_canal}\n{link}\n'

# 6. BALONMANO
for meta, link in canales_balonmano:
    nombre_canal = meta.split(",")[-1] if "," in meta else "Canal Balonmano"
    m3u_final += f'#EXTINF:-1 group-title="6. BALONMANO",{nombre_canal}\n{link}\n'

# Guardar el archivo limpio resultante
with open("parrilla_deportes_automatica.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_final)
