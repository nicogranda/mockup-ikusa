#!/usr/bin/env python3

"""
generar_portfolio.py
IKUSA — Mockup 1

Genera un mockup responsive con:
- Desktop
- Laptop
- Tablet
- Phone
- Logo del cliente
- Icono SEO opcional

IMPORTANTE:
El SEO NO sustituye ninguna pantalla.
Las cuatro pantallas siempre muestran la web real.
"""

import argparse
import sys
import urllib.request

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, ImageDraw, ImageChops
from playwright.sync_api import sync_playwright


# =========================================================
# ARCHIVOS
# =========================================================

SCRIPT_DIR = Path(__file__).resolve().parent

BASE_IMAGE_PATH = SCRIPT_DIR / "mockup_base.png"
SEO_ICON_PATH = SCRIPT_DIR / "seo_icon.png"


# =========================================================
# IKUSA MOCKUP 1 — 1200 × 710
# =========================================================

SCREEN_BOXES = {
    "desktop": (348, 90, 935, 426),
    "laptop":  (97, 342, 489, 575),
    "tablet":  (884, 294, 1105, 581),
    "phone":   (1043, 420, 1144, 625),
}


# =========================================================
# VIEWPORTS PARA PLAYWRIGHT
# =========================================================

VIEWPORTS = {

    "desktop": {
        "width": 1920,
        "height": 1100
    },

    "laptop": {
        "width": 1440,
        "height": 863
    },

    "tablet": {
        "width": 768,
        "height": 997
    },

    "phone": {
        "width": 390,
        "height": 854
    },
}


# =========================================================
# LOGO DEL CLIENTE
# =========================================================

# x0, y0, x1, y1
#
# Esta zona está separada de las pantallas.
# Luego podemos moverla unos píxeles después
# de ver el primer resultado real.

LOGO_BOX = (
    20,
    12,
    267,
    128
)


# =========================================================
# ICONO SEO
# =========================================================

# Solo aparecerá cuando:
#
# incluye_seo == True
#
# El archivo debe llamarse:
#
# seo_icon.png

SEO_ICON_MAX_SIZE = (
    62,
    46
)


# =========================================================
# ENTRADA INTERACTIVA
# =========================================================

def preguntar_datos(args):

    logo = args.logo

    if not logo:
        logo = input(
            "🖼 Logo del cliente — ruta local o URL (PNG o SVG): "
        ).strip()

    if args.seo is None:

        resp = input(
            "📈 ¿Se hizo trabajo de SEO para este cliente? (s/n): "
        ).strip().lower()

        incluye_seo = resp.startswith("s")

    else:

        incluye_seo = args.seo

    url = args.url or input(
        "🔗 URL del sitio a mockupear: "
    ).strip()

    output = args.output

    if not output:

        sugerido = "portfolio_resultado.png"

        resp = input(
            f"💾 Nombre del archivo de salida [{sugerido}]: "
        ).strip()

        output = resp or sugerido

    return url, logo, incluye_seo, output


# =========================================================
# FORZAR CARGA DE IMÁGENES LAZY
# =========================================================

def forzar_carga_lazy(page):

    page.evaluate(
        """
        () => new Promise((resolve) => {

            let total = 0;
            const step = 400;

            const timer = setInterval(() => {

                window.scrollBy(0, step);
                total += step;

                if (total >= document.body.scrollHeight) {

                    clearInterval(timer);

                    window.scrollTo(0, 0);

                    resolve();
                }

            }, 80);
        })
        """
    )


# =========================================================
# CAPTURAR WEB
# =========================================================

def capturar_screenshot(
    page,
    url: str,
    viewport: dict,
    wait_ms: int = 1500
) -> Image.Image:

    page.set_viewport_size(viewport)

    try:

        page.goto(
            url,
            wait_until="load",
            timeout=45000
        )

    except Exception:

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=45000
        )

    forzar_carga_lazy(page)

    page.wait_for_timeout(
        max(wait_ms, 500)
    )

    screenshot_bytes = page.screenshot(
        full_page=False
    )

    return Image.open(
        BytesIO(screenshot_bytes)
    ).convert("RGB")


# =========================================================
# AJUSTAR SCREENSHOT A LA PANTALLA
# =========================================================

def ajustar_a_pantalla(
    shot: Image.Image,
    box: tuple
) -> Image.Image:

    x0, y0, x1, y1 = box

    target_w = x1 - x0
    target_h = y1 - y0

    target_ratio = target_w / target_h
    src_ratio = shot.width / shot.height

    if src_ratio > target_ratio:

        new_width = int(
            shot.height * target_ratio
        )

        left = (
            shot.width - new_width
        ) // 2

        shot = shot.crop(
            (
                left,
                0,
                left + new_width,
                shot.height
            )
        )

    else:

        new_height = int(
            shot.width / target_ratio
        )

        top = max(
            0,
            (shot.height - new_height) // 2
        )

        shot = shot.crop(
            (
                0,
                top,
                shot.width,
                top + new_height
            )
        )

    return shot.resize(
        (
            target_w,
            target_h
        ),
        Image.Resampling.LANCZOS
    )


# =========================================================
# CONSTRUIR LOS CUATRO DISPOSITIVOS
# =========================================================

def construir_mockup_dispositivos(
    url: str
) -> Image.Image:

    fondo = Image.open(BASE_IMAGE_PATH).convert("RGB")
    base = fondo.copy()

    mascaras = {
        nombre: Image.open(SCRIPT_DIR / f"mask_{nombre}.png").convert("L")
        for nombre in SCREEN_BOXES
    }

    # La máscara antigua del móvil era rectangular y llegaba hasta el marco.
    # Construimos un cristal interior con esquinas redondeadas y margen visible.
    escala = 4
    cristal = Image.new(
        "L", (fondo.width * escala, fondo.height * escala), 0
    )
    ImageDraw.Draw(cristal).rounded_rectangle(
        (1043 * escala, 420 * escala, 1144 * escala - 1, 625 * escala - 1),
        radius=11 * escala, fill=255
    )
    mascaras["phone"] = cristal.resize(
        fondo.size, Image.Resampling.LANCZOS
    )

    # Siluetas independientes de los dispositivos delanteros. Se recupera
    # su marco original antes de pegar la captura de cada uno.
    siluetas = {}
    for nombre in ("laptop", "tablet", "phone"):
        mascara = Image.new("L", fondo.size, 0)
        dibujo = ImageDraw.Draw(mascara)
        if nombre == "laptop":
            dibujo.polygon(
                [(82, 320), (500, 320), (500, 585),
                 (546, 621), (39, 621), (82, 585)], fill=255
            )
        elif nombre == "tablet":
            dibujo.rounded_rectangle((866, 272, 1124, 609), radius=17, fill=255)
        else:
            dibujo.rounded_rectangle((1039, 409, 1157, 640), radius=15, fill=255)
        siluetas[nombre] = mascara

    # En la imagen original el móvil fue suavizado contra una pantalla blanca.
    # Extraemos la opacidad del marco oscuro para que los píxeles casi blancos
    # no formen un halo cuando detrás aparece la captura real de la tablet.
    oscuridad = ImageOps.grayscale(fondo).point(
        lambda valor: min(255, max(0, (245 - valor) * 2))
    )
    siluetas["phone"] = ImageChops.multiply(siluetas["phone"], oscuridad)

    with sync_playwright() as p:

        browser = p.chromium.launch()
        page = browser.new_page()

        for nombre, box in SCREEN_BOXES.items():

            if nombre in siluetas:
                base.paste(fondo, (0, 0), siluetas[nombre])

            if nombre == "phone":
                # El recorte deja visible parte del cristal blanco original.
                # Oscurecemos ese interior antes de insertar la nueva captura.
                ImageDraw.Draw(base).rounded_rectangle(
                    (1043, 417, 1148, 628), radius=13, fill=(17, 17, 18)
                )

            print(f"→ Capturando versión '{nombre}'...")

            shot = capturar_screenshot(
                page,
                url,
                VIEWPORTS[nombre]
            )

            shot = ajustar_a_pantalla(
                shot,
                box
            )

            layer = Image.new("RGB", base.size)
            layer.paste(shot, (box[0], box[1]))
            base.paste(
                layer,
                (0, 0),
                mascaras[nombre]
            )

        browser.close()

    return base


# =========================================================
# DETECTAR SVG
# =========================================================

def _es_svg(data_o_path) -> bool:

    if isinstance(
        data_o_path,
        (bytes, bytearray)
    ):

        return (
            b"<svg" in
            data_o_path[:1000].lower()
        )

    return str(
        data_o_path
    ).lower().endswith(".svg")


# =========================================================
# CONVERTIR SVG
# =========================================================

def _svg_a_imagen(
    svg_bytes: bytes,
    ancho_objetivo: int = 800
) -> Image.Image:

    try:

        import cairosvg

    except ImportError:

        raise RuntimeError(
            "El logo es SVG pero falta cairosvg.\n"
            "Instálala con:\n"
            "pip install cairosvg"
        )

    png_bytes = cairosvg.svg2png(
        bytestring=svg_bytes,
        output_width=ancho_objetivo
    )

    return Image.open(
        BytesIO(png_bytes)
    ).convert("RGBA")


# =========================================================
# CARGAR LOGO DEL CLIENTE
# =========================================================

def cargar_logo(
    logo_ref: str
) -> Image.Image:

    if logo_ref.lower().startswith(
        ("http://", "https://")
    ):

        print(
            f"→ Descargando logo desde {logo_ref}..."
        )

        req = urllib.request.Request(
            logo_ref,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            req,
            timeout=15
        ) as resp:

            data = resp.read()

        if (
            _es_svg(logo_ref)
            or
            _es_svg(data)
        ):

            return _svg_a_imagen(data)

        return Image.open(
            BytesIO(data)
        ).convert("RGBA")

    path = Path(logo_ref)

    if not path.exists():

        raise FileNotFoundError(
            f"No se encontró el logo en: {path}"
        )

    if _es_svg(path):

        return _svg_a_imagen(
            path.read_bytes()
        )

    return Image.open(
        path
    ).convert("RGBA")


# =========================================================
# COLOCAR LOGO DEL CLIENTE
# =========================================================

def colocar_logo(
    canvas: Image.Image,
    logo: Image.Image,
    box: tuple
) -> tuple[int, int, int, int]:

    x0, y0, x1, y1 = box

    box_w = x1 - x0
    box_h = y1 - y0

    logo_fit = ImageOps.contain(
        logo,
        (
            box_w,
            box_h
        )
    )

    px = (
        x0 +
        (box_w - logo_fit.width) // 2
    )

    py = (
        y0 +
        (box_h - logo_fit.height) // 2
    )

    canvas.alpha_composite(
        logo_fit,
        (
            px,
            py
        )
    )

    return (px, py, px + logo_fit.width, py + logo_fit.height)


# =========================================================
# COLOCAR ICONO SEO
# =========================================================

def colocar_icono_seo(
    canvas: Image.Image,
    logo_bounds: tuple = None
):

    if not SEO_ICON_PATH.exists():

        print(
            f"⚠️ No existe {SEO_ICON_PATH.name}. "
            "El mockup se generará sin icono SEO."
        )

        return

    seo_icon = Image.open(
        SEO_ICON_PATH
    ).convert("RGBA")

    # El PNG original tiene márgenes transparentes amplios.
    bounds = seo_icon.getbbox()
    if bounds is None:
        return
    seo_icon = seo_icon.crop(bounds)

    seo_icon.thumbnail(
        SEO_ICON_MAX_SIZE,
        Image.Resampling.LANCZOS
    )

    # Ubicarlo inmediatamente a la derecha del logo, sin entrar en la pantalla.
    x = max(logo_bounds[2] + 12, 205) if logo_bounds else 205
    x = min(x, 340 - seo_icon.width)
    y = max(14, (logo_bounds[1] + logo_bounds[3] - seo_icon.height) // 2) if logo_bounds else 38

    canvas.alpha_composite(
        seo_icon,
        (
            x,
            y
        )
    )


# =========================================================
# GENERAR PORTFOLIO
# =========================================================

def generar_portfolio(
    url: str,
    logo_ref: str,
    incluye_seo: bool,
    output_path: str
):

    # -----------------------------------------------------
    # Las 4 pantallas SIEMPRE muestran la web
    # -----------------------------------------------------

    devices = construir_mockup_dispositivos(
        url
    ).convert("RGBA")

    # -----------------------------------------------------
    # Logo del cliente
    # -----------------------------------------------------

    logo_bounds = None
    if logo_ref:

        logo = cargar_logo(
            logo_ref
        )

        logo_bounds = colocar_logo(
            devices,
            logo,
            LOGO_BOX
        )

    # -----------------------------------------------------
    # SEO
    #
    # NO modifica desktop
    # NO modifica laptop
    # NO modifica tablet
    # NO modifica móvil
    #
    # Solamente añade seo_icon.png
    # -----------------------------------------------------

    if incluye_seo:

        colocar_icono_seo(
            devices,
            logo_bounds
        )

    # -----------------------------------------------------
    # GUARDAR
    # -----------------------------------------------------

    devices.convert(
        "RGB"
    ).save(
        output_path,
        quality=95
    )

    print(
        f"\n✅ Portfolio guardado en: {output_path}"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Genera un mockup responsive "
            "para el portfolio de IKUSA."
        )
    )

    parser.add_argument(
        "--url",
        help="URL del sitio a mockupear"
    )

    parser.add_argument(
        "--logo",
        help=(
            "Ruta local o URL "
            "del logo del cliente"
        )
    )

    seo_group = (
        parser.add_mutually_exclusive_group()
    )

    seo_group.add_argument(
        "--seo",
        dest="seo",
        action="store_true",
        help="Añadir distintivo SEO"
    )

    seo_group.add_argument(
        "--no-seo",
        dest="seo",
        action="store_false",
        help="No añadir distintivo SEO"
    )

    parser.set_defaults(
        seo=None
    )

    parser.add_argument(
        "--output",
        help="Nombre del archivo de salida"
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # COMPROBAR BASE
    # -----------------------------------------------------

    if not BASE_IMAGE_PATH.exists():

        print(
            f"❌ Falta {BASE_IMAGE_PATH.name} "
            "en la carpeta del script."
        )

        sys.exit(1)

    # -----------------------------------------------------
    # DATOS
    # -----------------------------------------------------

    url, logo, incluye_seo, output = (
        preguntar_datos(args)
    )

    # -----------------------------------------------------
    # GENERAR
    # -----------------------------------------------------

    generar_portfolio(
        url,
        logo,
        incluye_seo,
        output
    )


if __name__ == "__main__":
    main()
