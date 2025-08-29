import pandas as pd
import getpass

# Leer el archivo Excel
path_file = "C:/Users/User/Desktop/Data_modified_order.xlsx"
chooice_sheet = "19"
df = pd.read_excel(path_file, chooice_sheet)

# Ordenar por apellido y luego por nombre
df[["Apellido", "Nombre"]] = df["Nombres"].str.split(
    " ", 1, expand=True
)  # Dividir en apellido y nombre

# Intercambiar el orden del apellido y el nombre
df["Nombre_completo"] = df.apply(
    lambda row: f"{row['Nombre']} {row['Apellido']}", axis=1
)

# df = df.sort_values(by=["Apellido", "Nombre"])  # Ordenar por apellido y luego por nombre

# Guardar el DataFrame ordenado en un nuevo archivo Excel
route_user = f"C:/Users/{getpass.getuser()}/Documents/order{chooice_sheet}.xlsx"
df.to_excel(route_user, sheet_name="Resultados_inidividuales", index=False)
print(
    "Se ha guardado satisfactoriamente su documento en la siguiente dirección:",
    route_user,
)
