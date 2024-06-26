import pandas as pd
import requests
import inquirer
import getpass
import re
import json
import time

name = list()
date = list()
dataUser = dict()
dataAlmacenar = []
logs = []
file_name = "blacklist_name"
BATCH_SIZE = 5000  # Tamaño del lote
MAX_RETRIES = 5  # Número máximo de reintentos

# Token
def get_token():
    try:
        with open("token.txt") as file:
            token_data = json.load(file)
        token = token_data["token"]
        expiration = token_data["expiration"]
        return token, expiration
    except (FileNotFoundError, KeyError):
        return None, None

def update_token(token, expires_in):
    expiration = time.time() + expires_in
    with open("token.txt", "w") as file:
        json.dump({"token": token, "expiration": expiration}, file)

def api_url(newData):
    count = len(newData[0])
    token, expiration = get_token()

    for start in range(0, count, BATCH_SIZE):
        end = min(start + BATCH_SIZE, count)
        batch_dataAlmacenar = []
        batch_logs = []

        for i in range(start, end):
            if token is None or time.time() >= expiration - 60:  # Renovar token si está a punto de caducar (1 minuto de margen)
                token = get_new_token()
                if token is None:
                    raise Exception("No se pudo obtener un nuevo token")
            
            url = f"https://veridocid.azure-api.net/api/blacklist"
            payload = {
                "id": f"batch-name-{i}",
                "name": f"{newData[0][i]}",
                "date_of_birth": f"{newData[1][i]}",
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }

            retries = 0
            while retries < MAX_RETRIES:
                try:
                    response = requests.post(url, headers=headers, json=payload)

                    if response.status_code == 401:  # Unauthorized
                        token = get_new_token()
                        if token is None:
                            raise Exception("No se pudo obtener un nuevo token")

                        headers["Authorization"] = f"Bearer {token}"
                        response = requests.post(url, headers=headers, json=payload)

                    response.raise_for_status()
                    jsonData = response.json()
                    batch_logs.append({"item": i, "data": jsonData})
                    print(json.dumps({"item": i, "data": jsonData}))

                    # Titles
                    no_data = "Sin datos"
                    name_title = "Nombre"
                    timestamp_title = "Hora y Fecha"
                    total_hits_title = "Resultado Global"
                    gender_title = "Género"
                    source_title = "Source Type"

                    if len(jsonData["found_records"]) > 0:
                        found_records = jsonData["found_records"][0]
                        gender = found_records["gender"]
                        source = found_records["source_type"]

                    batch_dataAlmacenar.append(
                        {
                            name_title: name[i],
                            timestamp_title: jsonData["timestamp"],
                            total_hits_title: jsonData["total_hits"],
                            source_title: source
                            if len(jsonData["found_records"]) > 0
                            else no_data,
                            gender_title: gender
                            if len(jsonData["found_records"]) > 0
                            else no_data,
                        }
                    )
                    break  # Salir del ciclo de reintentos si la petición fue exitosa
                except requests.exceptions.RequestException as err:
                    retries += 1
                    batch_logs.append({"item": i, "error": str(err), "retry": retries})
                    if retries >= MAX_RETRIES:
                        batch_dataAlmacenar.append(
                            {
                                name_title: name[i],
                                timestamp_title: no_data,
                                total_hits_title: str(err),
                                source_title: no_data,
                                gender_title: no_data,
                            }
                        )

        # Guardar progreso parcial
        batch_number = start // BATCH_SIZE + 1
        partial_file_name = f"{file_name}_partial_batch_{batch_number}"
        df = pd.DataFrame(batch_dataAlmacenar)
        df.to_excel(f"C:/Users/{getpass.getuser()}/Documents/{partial_file_name}.xlsx", sheet_name="Resultados_inidividuales", index=False)
        with open(f"{partial_file_name}.json", "w") as file:
            json.dump(batch_logs, file)

        # Agregar datos del lote al almacenamiento total
        dataAlmacenar.extend(batch_dataAlmacenar)
        logs.extend(batch_logs)

    # Crear DataFrame final
    df = pd.DataFrame(dataAlmacenar)
    print(df)

    # Guardar logs
    with open(f"{file_name}.json", "w") as file:
        json.dump(logs, file)

    # Guardar excel final
    route_user = f"C:/Users/{getpass.getuser()}/Documents/{file_name}.xlsx"
    df.to_excel(route_user, sheet_name="Resultados_inidividuales", index=False)
    print(
        "Se ha guardado satisfactoriamente su documento en la siguiente dirección:",
        route_user,
    )

def get_new_token():
    url = "https://veridocid.azure-api.net/api/auth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": "Ej4QpQ33HYwZ2JXYTLCf6c1li3vTLhjm",
        "client_secret": "DCpJ_-Bd2285RGBlTPEZkBh5_j-p7yZoMVUH2ei80FYPBkM7yGH4WvNvhX_NA88m",
        "audience": "veridocid",
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        new_token = token_data["access_token"]
        expires_in = token_data["expires_in"]  # Obtener tiempo de expiración
        update_token(new_token, expires_in)
        return new_token
    except requests.exceptions.RequestException as err:
        print(f"Error al obtener el nuevo token: {err}")
        return None

def validate_input_path(value):
    regex_path = "[a-zA-Z]:[\\\/](?:[a-zA-Z0-9\-\_\.\¿'\¡\{\}\[\]\,\!\+\´\$\#\%\(\)\&\=]+[\\\/])*([a-zA-Z0-9\-\_\.\¿'\¡\{\}\[\]\,\!\+\´\$\#\%\(\)\&\=]+\.xlsx)"
    resultado = re.search(regex_path, value)
    return resultado

validate = False

print(
    "Ingrese la ruta del archivo (e.j.: C:/Users/User/Desktop/name2_file.xlsx): ",
    end="",
)

# Until a correct route is entered
while not validate:
    path_file = input()
    validate = validate_input_path(path_file)
    if not validate:
        print("Lo sentimos, debemos introducir una ruta válida: ", end="")

# Select the sheet in the file excel
xl = pd.ExcelFile(path_file)
sheet_names = xl.sheet_names
questions = [
    inquirer.List(
        "sheetDocs",
        message="Eliga la hoja del documento para obtener los datos",
        choices=sheet_names,
    ),
]
chooice_sheet = inquirer.prompt(questions)

# Read the excel file
reader = pd.read_excel(path_file, chooice_sheet["sheetDocs"])

# Data user
dataUser = []
for column in reader.columns:
    if column == "Nombres":
        name = reader[column].tolist()
    if column == "NACIMIENTO":
        date = reader[column].tolist()

dataUser = [name, date]

# Call API
api_url(dataUser)
