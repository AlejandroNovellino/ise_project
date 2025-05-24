"""
Utils for the project.
"""

import os
import requests
import threading
import time
import random
import pandas as pd
from dotenv import load_dotenv


# variables for working between functions ------------------------------------------------
# headers for the requests
global_headers = {
    "Authorization": None,
    "Content-Type": "application/json"
}

# variables to save the results
results_lock = threading.Lock()
concurrent_test_results = []
concurrent_test_individual_results = {
    'user_ids': [],
    'endpoints': [],
    'status_codes': [],
    'latencies': [],
    'times': [], # Para registrar el tiempo en que se realizó la petición
    'error_intervals': []
}


# functions ------------------------------------------------------------------------------
# function to get the access token
def get_access_token(client_id, client_secret):
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()

        print('✅ Token loaded.')

        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener el token de acceso: {e}")
        return None


def configure_headers():
    """
    Configure the headers for the requests.
    """

    # environment variables load
    load_dotenv()

    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

    # get the access token
    ACCESS_TOKEN = get_access_token(CLIENT_ID, CLIENT_SECRET)
    if not ACCESS_TOKEN:
        print("No se pudo obtener el token de acceso. Las pruebas no pueden continuar.")
        exit()

    # set the global headers
    global_headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"


def user_simulation_task(user_id, endpoint, num_requests_per_user):
    """
    Simula el comportamiento de un único usuario haciendo peticiones a un endpoint.
    """

    user_results = {
        'user_id': user_id,
        'endpoint': endpoint,
        'total_requests': 0,
        'successful_requests': 0,
        'error_4xx_requests': 0,
        'error_5xx_requests': 0,
        'total_response_time': 0,
        'latencies': [], # Para registrar tiempos de respuesta individuales
        'errors_occurred': [], # Para registrar códigos de error
        'test_duration': 0
    }

    user_ids = []
    endpoints = []
    status_codes = []
    latencies = []
    times = []

    # variables for saving the error interval values
    last_error_time = None
    error_intervals = []

    # test info
    test_start_time = time.time()
    print(f"✴️ Usuario {user_id} - Starting requests to {endpoint}. - Test started at {test_start_time}")

    # do requests for the given amount
    for i in range(num_requests_per_user):

        start_time = time.time()

        try:
            # request
            response = requests.get(endpoint, headers=global_headers)

            # ☑️ save the data to study

            #   save the whole test results
            duration = time.time() - start_time
            user_results['total_requests'] += 1
            user_results['total_response_time'] += duration
            user_results['latencies'].append(duration)
            status_code = response.status_code

            #   save the individual test results
            user_ids.append(user_id)
            endpoints.append(endpoint)
            status_codes.append(status_code)
            latencies.append(duration)
            times.append(time.time()) # save the time in floating point

            if 200 <= status_code < 300: # if request successful
                user_results['successful_requests'] += 1

                # set the interval error to None, because there was no error
                error_intervals.append(None)

            elif 400 <= status_code < 500: # if request of kind 4xx
                user_results['error_4xx_requests'] += 1
                user_results['errors_occurred'].append(status_code)

                if status_code == 429: # if request of kind 429 (to many requests)
                    print(f"Usuario {user_id} - Alerta: Recibido 429 (Too Many Requests).")

                if last_error_time: # if there was a previous error
                    # calculate the interval between errors
                    error_intervals.append(time.time() - last_error_time)
                else:
					# save none because there was no previous error
                    error_intervals.append(None)

                last_error_time = time.time() # update the last error time

            elif 500 <= status_code < 600:
                user_results['error_5xx_requests'] += 1
                user_results['errors_occurred'].append(status_code)
                print(f"Usuario {user_id} - Error 5xx ({status_code}) en {endpoint}.")

                if last_error_time: # if there was a previous error
                    # calculate the interval between errors
                    error_intervals.append(time.time() - last_error_time)
                else:
					# save none because there was no previous error
                    error_intervals.append(None)

                last_error_time = time.time() # update the last error time

        except requests.exceptions.RequestException as e:
            user_results['total_requests'] += 1 # Contar también las peticiones con excepción
            user_results['errors_occurred'].append(str(e)) # Registrar la excepción
            print(f"Usuario {user_id} - Excepción de red para {endpoint}: {e}")

        finally:
            time.sleep(1) # wait 1 second before the next request

    test_finish_time = time.time()
    test_duration = test_finish_time - test_start_time

    # save the test duration
    user_results['test_duration'] = test_duration

    print(f"✅ User {user_id} - Finished requests to {endpoint}. - Test finished at {test_finish_time}. Duration: {test_duration:.2f}s")

    # add the results to the global results
    with results_lock:
        # save the whole test results
        concurrent_test_results.append(user_results)
        # save the individual test results
        concurrent_test_individual_results['user_ids'].extend(user_ids)
        concurrent_test_individual_results['endpoints'].extend(endpoints)
        concurrent_test_individual_results['status_codes'].extend(status_codes)
        concurrent_test_individual_results['latencies'].extend(latencies)
        concurrent_test_individual_results['times'].extend(times)
        concurrent_test_individual_results['error_intervals'].extend(error_intervals)


def simulate_concurrent_users(num_users, num_requests_per_user, endpoints_to_test):
    """
    Orquesta la simulación de múltiples usuarios concurrentes.

    Args:
        num_users (int): El número de usuarios a simular.
        num_requests_per_user (int): El número de peticiones que cada usuario hará.
        endpoints_to_test (list): Lista de endpoints a los que los usuarios harán peticiones.
                                  Los usuarios se distribuirán entre estos endpoints.
    """

    print(f"\n--- Simulation started with {num_users} concurrent users ---")
    print(f"Each user will do {num_requests_per_user} requests.\n")

    threads = []

    # create a thread for each user
    endpoint_index = 0

    for i in range(num_users):
        # select the endpoint for the user
        selected_endpoint = endpoints_to_test[endpoint_index % len(endpoints_to_test)]

        # create the thread
        thread = threading.Thread(
            target=user_simulation_task,
            args=(i + 1, selected_endpoint, num_requests_per_user)
        )
        threads.append(thread)
        thread.start() # Inicia el hilo
        endpoint_index += 1

        # wait i little for the next thread
        time.sleep(random.uniform(0.01, 0.1))

    # wait to each thread to finish
    for thread in threads:
        thread.join()

    print("\n--- Simulation finished ---")


def process_concurrent_results():
    """
    Consolida y analiza los resultados de la simulación de usuarios concurrentes.
    """
    if not concurrent_test_results:
        print("No hay resultados para procesar de la simulación concurrente.")
        return

    df_concurrent = pd.DataFrame(concurrent_test_results)
    df_concurrent_2 = pd.DataFrame(concurrent_test_individual_results)

    # global calculates
    global_total_requests = df_concurrent['total_requests'].sum()
    global_successful_requests = df_concurrent['successful_requests'].sum()
    global_error_4xx_requests = df_concurrent['error_4xx_requests'].sum()
    global_error_5xx_requests = df_concurrent['error_5xx_requests'].sum()
    global_success_rate = (global_successful_requests / global_total_requests) * 100 if global_total_requests > 0 else 0
    global_error_4xx_rate = (global_error_4xx_requests / global_total_requests) * 100 if global_total_requests > 0 else 0
    global_error_5xx_rate = (global_error_5xx_requests / global_total_requests) * 100 if global_total_requests > 0 else 0

    # global results
    print("\n--- Resumen General de la Simulación Concurrente ---")
    print(f"Total de usuarios simulados: {len(df_concurrent)}")
    print(f"Peticiones totales realizadas: {df_concurrent['total_requests'].sum()}")
    print(f"Peticiones exitosas totales: {df_concurrent['successful_requests'].sum()}")
    print(f"Errores 4xx totales: {df_concurrent['error_4xx_requests'].sum()}")
    print(f"Errores 5xx totales: {df_concurrent['error_5xx_requests'].sum()}")
    print(f"Tasa de éxito global: {global_success_rate:.2f}%")
    print(f"Tasa de error 4xx global: {global_error_4xx_rate:.2f}%")
    print(f"Tasa de error 5xx global: {global_error_5xx_rate:.2f}%")

    # analysis by endpoint
    agg_by_endpoint = df_concurrent.groupby('endpoint').agg(
        total_requests=('total_requests', 'sum'),
        successful_requests=('successful_requests', 'sum'),
        error_4xx_requests=('error_4xx_requests', 'sum'),
        error_5xx_requests=('error_5xx_requests', 'sum'),
        avg_latency=('latencies', lambda x: pd.Series([item for sublist in x for item in sublist]).mean()),
        num_users=('user_id', 'nunique')
    ).reset_index()

    agg_by_endpoint['success_rate'] = (agg_by_endpoint['successful_requests'] / agg_by_endpoint['total_requests']) * 100
    agg_by_endpoint['error_4xx_rate'] = (agg_by_endpoint['error_4xx_requests'] / agg_by_endpoint['total_requests']) * 100
    agg_by_endpoint['error_5xx_rate'] = (agg_by_endpoint['error_5xx_requests'] / agg_by_endpoint['total_requests']) * 100

    return df_concurrent, df_concurrent_2, agg_by_endpoint
