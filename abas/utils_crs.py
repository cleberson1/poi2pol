"""Funções de sistema de coordenadas compartilhadas pelas abas."""


def crs_geografico(datum: str) -> str:
    """CRS em graus decimais para o datum escolhido."""
    return "EPSG:4674" if datum == "SIRGAS 2000" else "EPSG:4326"


def fuso_utm(lon: float) -> int:
    """Fuso UTM (1-60) a partir da longitude."""
    return min(max(int((lon + 180) // 6) + 1, 1), 60)


def crs_utm(zona: int, hemisferio: str, datum: str) -> str:
    """CRS UTM (código EPSG quando existir; senão string PROJ equivalente)."""
    sul = hemisferio.upper() == "S"
    if datum == "SIRGAS 2000":
        if sul and 17 <= zona <= 25:
            return f"EPSG:{31960 + zona}"
        if not sul and 11 <= zona <= 22:
            return f"EPSG:{31954 + zona}"
        return (
            f"+proj=utm +zone={zona} {'+south ' if sul else ''}"
            "+ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs"
        )
    return f"EPSG:{(327 if sul else 326) * 100 + zona}"
