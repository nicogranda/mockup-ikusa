# Mockup Ikusa

Generador de mockups para portfolio. El formulario PHP invoca Python con Playwright y Pillow. No utiliza base de datos.

## Instalación

```bash
git clone https://github.com/nicogranda/mockup-ikusa.git
cd mockup-ikusa
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m playwright install chromium
php -S localhost:8000
```

Abre http://localhost:8000/index.php. PHP debe tener habilitada la función `exec` y permisos de escritura en `clientes/`. Los resultados se guardan allí.

## Conectar una carpeta local existente

```bash
cd /ruta/a/tu/mockup
git init
git branch -M main
git remote add origin https://github.com/nicogranda/mockup-ikusa.git
git fetch origin
```

Para incorporar el contenido remoto sin sobrescribir archivos locales, revisa primero las diferencias con `git diff origin/main` y decide qué archivos conservar.
