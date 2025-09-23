import pandas as pd
import requests
import inquirer
import getpass
import openpyxl
import sys
import re
import json

# reader = pd.read_excel("C:/Users/User/Desktop/test_dilisense.xlsx", "Hoja1")
#reader = pd.read_excel("C:/Users/User/Desktop/test_dilisense.xlsx", "Hoja2")

# data = reader.head()

name = list()
date = list()
dataUser = dict()
dataAlmacenar = []
logs = []


def api_url(newData):
    count = len(newData[0])
    #Pass the name and the date of birthday
    for i in range(0, count):
        batch_logs = []
        batch_dataAlmacenar = []
        
        url = f'https://api.dilisense.com/v1/checkIndividual?names={newData[0][i]}&fuzzy_search=1&dob={newData[1][i]}'
        payload = {}

        headers = {
            'x-api-key': 'cqfHRgMJgK3QMgNaPoXzD1ycLM71uU556ilWvIb6'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        # print(response.text)
        jsonData = response.json()
        batch_logs.append({"item": i, "data": jsonData})
        print(json.dumps({"item": i, "data": jsonData}))

        # Titles
        no_data = "Sin datos"
        name_title = "Nombre"
        timestamp_title = "Hora y Fecha"
        total_hits_title = "Resultado Global"
        gender_title = "Género"
        date_of_birth_title = "Fecha de Nacimiento"
        citizenship_title = "Ciudadanía"
        source_type_title = "Tipo de fuente"
        given_names_title = "Nombres de Pila"
        description_title = "Descripción"
        occupations_title = "Ocupación"
        place_of_birth_title = "Lugar de Nacimiento"
        entity_type_title = "Tipo de Entidad"
        pep_type_title = "Tipo de PEP"
        name_found_title = "Coincidencias de nombre"
        source_id_title = "Fuente"
        links_title = "Links"

        # print(jsonData["found_records"])

        if(len(jsonData["found_records"]) > 0):
            found_records = jsonData["found_records"][0]
            gender = found_records["gender"]
            date_of_birth = found_records["date_of_birth"]
            citizenship = found_records["citizenship"] if "citizenship" in found_records else no_data
            source_type = found_records["source_type"]
            given_names = found_records["given_names"] if "given_names" in found_records else no_data
            description = found_records["description"] if "description" in found_records else no_data
            occupations = found_records["occupations"] if "occupations" in found_records else no_data
            place_of_birth = found_records["place_of_birth"] if "place_of_birth" in found_records else no_data
            pep_type = found_records["pep_type"] if "pep_type" in found_records else no_data
            entity_type = found_records["entity_type"] if "entity_type" in found_records else no_data
            name_found = found_records["name"]
            source_id = found_records["source_id"]

        """ if(len(jsonData["found_records"]) > 1):
            links = jsonData["found_records"][0]["links"] """

        batch_dataAlmacenar.append(
            {name_title: name[i],
             timestamp_title: jsonData["timestamp"],
             total_hits_title: jsonData["total_hits"],
             gender_title: gender if len(jsonData["found_records"]) > 0 else no_data,
             })

        """ 
        This data should be to inside the batch_dataAlmacenar.append
        
        date_of_birth_title: date_of_birth if len(jsonData["found_records"]) > 0 else no_data,
        citizenship_title: citizenship if len(jsonData["found_records"]) > 0 else no_data,
        source_type_title: source_type if len(jsonData["found_records"]) > 0 else no_data,
        given_names_title: given_names if len(jsonData["found_records"]) > 0 else no_data,
        description_title: description if len(jsonData["found_records"]) > 0 else no_data,
        occupations_title: occupations if len(jsonData["found_records"]) > 0 else no_data,
        place_of_birth_title: place_of_birth if len(jsonData["found_records"]) > 0 else no_data,
        entity_type_title: entity_type if len(jsonData["found_records"]) > 0 else no_data,
        pep_type_title: pep_type if len(jsonData["found_records"]) > 0 else no_data,
        name_found_title: name_found if len(jsonData["found_records"]) > 0 else no_data,
        source_id_title: source_id if len(jsonData["found_records"]) > 0 else no_data,
        links_title: links if len(jsonData["found_records"]) > 1 else no_data, """

        # Agregar datos del lote al almacenamiento total
        dataAlmacenar.extend(batch_dataAlmacenar)
        logs.extend(batch_logs)
        
    # Create DataFrame
    df = pd.DataFrame(dataAlmacenar)
    # print(data)
    print(df)

    # Guardar logs
    with open(f"Resultados.json", "w") as file:
        json.dump(logs, file)

    # Save excel
    route_user = 'C:/Users/'+getpass.getuser() + '/Desktop/Resultados.xlsx'
    df.to_excel(route_user, sheet_name='Resultados_inidividuales')
    print("Se ha guardado satisfactoriamente su documento en la siguiente dirección:", route_user)


# print(reader["Name"])

# Introduce the path file
def validate_input_path(value):
    regex_path = r"[a-zA-Z]:[\\\/](?:[a-zA-Z0-9\-\_\.\¿'\¡\{\}\[\]\,\!\+\´\$\#\%\(\)\&\=]+[\\\/])*([a-zA-Z0-9\-\_\.\¿'\¡\{\}\[\]\,\!\+\´\$\#\%\(\)\&\=]+\.xlsx)"
    resultado = re.search(regex_path, value)
    return resultado


validate = False

print('Ingrese la ruta del archivo (e.j.: C:/Users/User/Desktop/name_file.xlsx): ', end='')

# Until a correct route is entered
while not validate:
    path_file = input()
    validate = validate_input_path(path_file)
    if not validate:
        print('Lo sentimos, debemos introducir una ruta válida: ', end='')

# Select the sheet in the file excel
xl = pd.ExcelFile(path_file)
xl.sheet_names
questions = [
    inquirer.List('sheetDocs',
                  message="Eliga la hoja del documento para obtener los datos",
                  choices=xl.sheet_names,
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
    if column == "NACIMIENTO":
        date = reader[column].tolist()

dataUser = [name, date]

# Call API
# print(dataUser)
api_url(dataUser)
