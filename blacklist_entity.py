import pandas as pd
import requests
import inquirer
import getpass
import re
import json

name = list()
dataUser = dict()
dataAlmacenar = []
logs = []
file_name = "blacklist_entity_CredencialesLeaseForU"


# Token
def get_token():
    with open("token.txt") as file:
        token = file.readline().strip()

    return token


def update_token(token):
    with open("token.txt", "w") as file:
        file.write(token)


def api_url(newData):
    count = len(newData[0])
    token = get_token()

    # Pass the names
    for i in range(0, count):
        url = f"https://veridocid.azure-api.net/api/blacklistentity"
        payload = {"id": f"batch-{i}", "names": f"{newData[0][i]}"}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 401:  # Unauthorized
                # Obtener un nuevo token
                new_token = get_new_token()
                if new_token is None:
                    raise Exception("No se pudo obtener un nuevo token")

                # Actualizar el token en el archivo "token.txt"
                update_token(new_token)
                token = new_token

                # Reintentar la solicitud con el nuevo token
                headers["Authorization"] = f"Bearer {new_token}"
                response = requests.post(url, headers=headers, json=payload)

            response.raise_for_status()
            jsonData = response.json()
            logs.append({"item": i, "data": jsonData})
            print(json.dumps({"item": i, "data": jsonData}))

            # Titles
            no_data = "Sin datos"
            name_title = "Nombre"
            timestamp_title = "Hora y Fecha"
            total_hits_title = "Resultado global"
            entity_type_title = "Tipo de entidad"
            source_title = "Source Type"

            if len(jsonData["found_records"]) > 0:
                found_records = jsonData["found_records"][0]
                entity_type = found_records["entity_type"]
                source = found_records["source_type"]

            dataAlmacenar.append(
                {
                    name_title: name[i],
                    timestamp_title: jsonData["timestamp"],
                    total_hits_title: jsonData["total_hits"],
                    source_title: source
                    if len(jsonData["found_records"]) > 0
                    else no_data,
                    entity_type_title: entity_type
                    if len(jsonData["found_records"]) > 0
                    else no_data,
                }
            )
        except requests.exceptions.RequestException as err:
            logs.append({"item": i, "error": str(err)})
            dataAlmacenar.append(
                {
                    name_title: name[i],
                    timestamp_title: no_data,
                    total_hits_title: str(err),
                    source_title: no_data,
                    entity_type_title: no_data,
                }
            )

    # Create DataFrame
    df = pd.DataFrame(dataAlmacenar)
    # df = df.append(dataAlmacenar, ignore_index=True)
    print(df)

    # Save logs
    with open(f"{file_name}.json", "w") as file:
        json.dump(logs, file)

    # Save excel
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
        return new_token
    except requests.exceptions.RequestException as err:
        print(f"Error al obtener el nuevo token: {err}")
        return None


# Introduce the path file
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
# print(reader)

# Data user
dataUser = []
for column in reader.columns:
    if column == "Nombres":
        name = reader[column].tolist()

dataUser = [name]

# Call API
api_url(dataUser)
