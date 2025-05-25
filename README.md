# Pruebas de Latencia y Límite de Tasa de la API de Spotify

Este proyecto contiene un conjunto de experimentos y utilidades para probar la latencia, los límites de tasa y las tasas de error de varios endpoints de la API de Spotify bajo diferentes condiciones y escenarios de red.

## Estructura del Proyecto

```
.
├── 1-objective-A.ipynb
├── 2-objective-A.ipynb
├── 3-objective-B.ipynb
├── 4-objective-C.ipynb
├── 5-objective-BC.ipynb
├── requirements.txt
├── utils.py
├── files/
│   ├── obj-A/
│   ├── obj-B/
│   ├── obj-C/
│   └── obj-BC/
├── .env
├── .env.example
├── .gitignore
├── .vscode/
└── .idea/
```

- **1-objective-A.ipynb**: Prueba base inicial para los endpoints de la API de Spotify.
- **2-objective-A.ipynb**: Prueba base extendida con agregación y exportación de resultados.
- **3-objective-B.ipynb**: Pruebas de latencia con VPN.
- **4-objective-C.ipynb**: Pruebas de latencia con una red de 10 Mbps.
- **5-objective-BC.ipynb**: Pruebas combinadas para los objetivos B y C.
- **utils.py**: Funciones utilitarias para autenticación, simulación de solicitudes y recopilación de resultados.
- **files/**: Archivos CSV de salida para cada objetivo y ejecución de prueba.

## Configuración

1. **Clona el repositorio** e instala las dependencias:

   ```sh
   pip install -r requirements.txt
   ```

2. **Variables de Entorno**  
   Copia `.env.example` a `.env` y completa tus credenciales de la API de Spotify:

   ```
   CLIENT_ID=tu_spotify_client_id
   CLIENT_SECRET=tu_spotify_client_secret
   ```

3. **Ejecuta los Notebooks**  
   Abre los notebooks de Jupyter (`*.ipynb`) en VS Code o Jupyter Lab y ejecuta las celdas según sea necesario para cada objetivo.

## Salida

Los resultados se guardan como archivos CSV en los directorios `files/obj-*`:

- `global_results.csv`: Resultados agregados para todos los usuarios/endpoints.
- `individual_results.csv`: Resultados por usuario y por endpoint.
- `endpoints_results.csv`: Resultados agregados por endpoint.

## Utilidades

- [`utils.py`](utils.py): Contiene funciones para autenticación, configuración de cabeceras y tareas de simulación de usuarios.

## Requisitos

- Python 3.12+
- Consulta [`requirements.txt`](requirements.txt) para ver las dependencias.

## Licencia

Este proyecto es para fines educativos y de investigación.
