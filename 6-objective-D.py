import time
import psutil
from playwright.sync_api import sync_playwright


def get_browser_process_id(browser_name="chrome"):
    """Intenta encontrar el PID del proceso del navegador."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if browser_name in proc.name().lower() or any(
                browser_name in arg.lower() for arg in proc.cmdline()
            ):
                return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None


def measure_spotify_performance(url, duration_seconds=60, sample_interval_seconds=1):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )  # Puedes cambiar a headless=True para no ver el navegador
        page = browser.new_page()

        print(f"Abriendo la URL: {url}")
        page.goto(url)

        # Esperar a que el SDK de Spotify cargue y el reproductor esté listo
        time_to_wait = 10
        print(f"Esperando {time_to_wait} segundos para que cargue la página y el SDK.")
        time.sleep(time_to_wait)  # Ajusta esto según sea necesario

        # Encontrar el PID del proceso del navegador
        browser_pid = get_browser_process_id("msedge")  # O "firefox>", "msedge"
        if not browser_pid:
            print(
                "No se pudo encontrar el PID del proceso del navegador. No se monitoreará el uso de recursos."
            )
            browser.close()
            return

        print(f"Monitoreando el proceso del navegador con PID: {browser_pid}")
        browser_process = psutil.Process(browser_pid)

        # Inicia la reproducción
        try:
            # Haz clic en el botón de play con Id 'togglePlay'
            page.click("#togglePlay")
            print("Simulando inicio de reproducción...")

        except Exception as e:
            print(f"No se pudo interactuar con el botón de play: {e}")

        cpu_usages = []
        memory_usages_mb = []

        start_time = time.time()
        while (time.time() - start_time) < duration_seconds:
            try:
                cpu_percent = browser_process.cpu_percent(
                    interval=sample_interval_seconds
                )
                memory_info = browser_process.memory_info()
                memory_rss_mb = memory_info.rss / (1024 * 1024)

                cpu_usages.append(cpu_percent)
                memory_usages_mb.append(memory_rss_mb)

                print(
                    f"Tiempo: {int(time.time() - start_time)}s - CPU: {cpu_percent:.2f}% - Memoria: {memory_rss_mb:.2f} MB"
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                print(
                    "El proceso del navegador terminó inesperadamente o no se pudo acceder."
                )
                break
            time.sleep(
                sample_interval_seconds
            )  # Esperar antes de la siguiente medición

        print("\nResultados del monitoreo:")
        if cpu_usages:
            print(f"Uso promedio de CPU: {sum(cpu_usages) / len(cpu_usages):.2f}%")
            print(f"Uso máximo de CPU: {max(cpu_usages):.2f}%")
        if memory_usages_mb:
            print(
                f"Uso promedio de Memoria: {sum(memory_usages_mb) / len(memory_usages_mb):.2f} MB"
            )
            print(f"Uso máximo de Memoria: {max(memory_usages_mb):.2f} MB")

        browser.close()


WEB_PAGE_URL = "http://127.0.0.1:5500/index.html"  # URL de la página web que contiene el SDK de Spotify
MEASUREMENT_DURATION = 180  # Duración de la medición en segundos
SAMPLE_INTERVAL = 1  # Intervalo entre mediciones en segundos

if __name__ == "__main__":
    measure_spotify_performance(WEB_PAGE_URL, MEASUREMENT_DURATION, SAMPLE_INTERVAL)
