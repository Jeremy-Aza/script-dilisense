import pandas as pd
from pandas.io import json
import requests

# reader = pd.read_excel("C:/Users/User/Desktop/test_dilisense.xlsx", "Hoja1")
reader = pd.read_excel(
    "C:/Users/User/Desktop/test_dilisense.xlsx", "Hoja2")

# data = reader.head()

name = dict()
data = []


def api_url(name):
    for index in range(0, len(name)):
        url = f'https://api.dilisense.com/v1/checkIndividual?names={name[index]}&fuzzy_search=1'
        payload = {}

        headers = {
            'x-api-key': 'cqfHRgMJgK3QMgNaPoXzD1ycLM71uU556ilWvIb6'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        # print(response.text)
        jsonData = response.json()
        # print(jsonData)

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
        other_information_title = "Otra Información"
        links_title = "Links"

        # print(jsonData["found_records"][0])

        if(len(jsonData["found_records"]) > 0):
            # print(jsonData["found_records"][0]["sanction_details"])
            found_records = jsonData["found_records"][0]
            gender = found_records["gender"]
            date_of_birth = found_records["date_of_birth"]
            citizenship = found_records["citizenship"]
            source_type = found_records["source_type"]
            given_names = found_records["given_names"]
            description = jsonData["found_records"][1]["description"]
            occupations = jsonData["found_records"][1]["occupations"]
            place_of_birth = jsonData["found_records"][1]["place_of_birth"]
            pep_type = jsonData["found_records"][1]["pep_type"]
            entity_type = found_records["entity_type"]
            name_found = found_records["name"]
            source_id = found_records["source_id"]
            links = found_records["links"]

        data.append(
            {name_title: name[index],
             timestamp_title: jsonData["timestamp"],
             total_hits_title: jsonData["total_hits"],
             gender_title: gender if len(jsonData["found_records"]) > 0 else no_data,
             date_of_birth_title: date_of_birth[0] if len(jsonData["found_records"]) > 0 else no_data,
             citizenship_title: citizenship if len(jsonData["found_records"]) > 0 else no_data,
             source_type_title: source_type if len(jsonData["found_records"]) > 0 else no_data,
             given_names_title: given_names if len(jsonData["found_records"]) > 0 else no_data,
             description_title: description if len(jsonData["found_records"]) > 0 else no_data,
             occupations_title: occupations if occupations else no_data if len(jsonData["found_records"]) > 0 else no_data,
             place_of_birth_title: place_of_birth if len(jsonData["found_records"]) > 0 else no_data,
             entity_type_title: entity_type if len(jsonData["found_records"]) > 0 else no_data,
             pep_type_title: pep_type if len(jsonData["found_records"]) > 0 else no_data,
             name_found_title: name_found if len(jsonData["found_records"]) > 0 else no_data,
             source_id_title: source_id if len(jsonData["found_records"]) > 0 else no_data,
             links_title: links if len(jsonData["found_records"]) > 0 else no_data,
             })

    # Create DataFrame
    df = pd.DataFrame()
    # print(data)
    df = df.append(data, ignore_index=True)
    print(df)

    # Save excel
    df.to_excel('testing.xlsx', sheet_name='example')


# print(reader["Name"])

for tags, contenido in reader.items():
    if(tags == "Name" or tags == "Nombre"):
        # print(contenido.to_dict())
        # Call API
        api_url(contenido.to_list())


""" print(list(reader.get("Name").values))
print(list(reader.get("Gender").values)) """
