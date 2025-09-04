# It reads an Excel and a JSON file, applies the matching logic you described,
# and writes an output Excel with the matched results.

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Union
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
import pandas as pd
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Union
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
import pandas as pd


def strip_accents(text: str) -> str:
    # Quita acentos/diacríticos
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in nfkd if unicodedata.category(ch) != "Mn")


_word_re = re.compile(r"[A-Za-z0-9ÁÉÍÓÚÜÑáéíóúüñ]+", re.UNICODE)


def tokenize_name(name: str) -> List[str]:
    """
    - Pasa a minúsculas
    - Quita acentos
    - Extrae solo tokens alfanuméricos (con soporte básicas para ñ/acentos)
    - Mantiene multiplicidad de palabras (Counter) para comparación exacta en cantidad
    """
    if not isinstance(name, str):
        name = "" if name is None else str(name)
    # Mantener letras/nums, eliminar signos, normalizar acentos
    # Primero extraer tokens para soportar ñ y acentos, luego quitar acentos
    tokens_raw = _word_re.findall(name)
    tokens = [strip_accents(t).lower() for t in tokens_raw if t]
    return tokens


def tokens_equal(a: Iterable[str], b: Iterable[str]) -> bool:
    return Counter(a) == Counter(b)


def normalize_timestamp(ts: Union[str, datetime]) -> str:
    """
    Normaliza timestamps a ISO-8601 con 'Z' cuando sea posible.
    Si no se puede parsear, devuelve el string tal cual, sin espacios extra.
    """
    if isinstance(ts, datetime):
        # Convertir a UTC-like sin tz info explícita (asumimos ya es UTC si viene con Z).
        return ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    if not isinstance(ts, str):
        ts = "" if ts is None else str(ts)
    ts = ts.strip()
    if not ts:
        return ts
    # Aceptar formatos comunes ISO, con o sin Z
    # Reemplazar espacio por 'T' si viene con espacio
    ts2 = ts.replace(" ", "T")
    # Si termina con Z, Python no lo parsea directo sin reemplazo
    try:
        if ts2.endswith("Z"):
            dt = datetime.fromisoformat(ts2.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            dt = datetime.fromisoformat(ts2)
            # Si no tiene tz, lo tomamos tal cual y marcamos Z (asumimos UTC)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        # Si falla, devolvemos el string original (pero sin espacios)
        return ts


def load_json_records(json_path: Path) -> List[Dict[str, Any]]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # El archivo puede ser una lista de items o algún dict contenedor.
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        # Tratar de encontrar una lista plausible dentro del dict
        for key in ("items", "results", "data", "list", "records"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # Si no hay, devolver en formato homogenizado si parece ser un item único
        return [data]
    else:
        raise ValueError("Formato JSON no soportado: se esperaba lista o dict")


def bulletify(value: Any) -> str:
    """
    Convierte listas de strings a viñetas con '* ' por línea.
    Si es dict u otro tipo, regresa JSON compactado. Si es string, lo devuelve tal cual.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        # flatear elementos a string
        items = []
        for v in value:
            if isinstance(v, (dict, list)):
                items.append(json.dumps(v, ensure_ascii=False))
            elif v is None:
                continue
            else:
                s = str(v).strip()
                if s:
                    items.append(s)
        if not items:
            return ""
        return "" + "\n* ".join(items)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def main(excel_path: Path, json_path: Path, out_path: Path) -> None:
    # Leer Excel
    df = pd.read_excel(excel_path, dtype=str)  # leemos como string para controlar parsing
    # Normalizar nombres de columnas (quitar espacios duplicados)
    cols_norm = {c: re.sub(r"\s+", " ", str(c)).strip() for c in df.columns}
    df.rename(columns=cols_norm, inplace=True)

    # Columnas esperadas
    col_nombre = next((c for c in df.columns if c.lower() == "nombre"), None)
    col_ts = next((c for c in df.columns if c.lower() in ("hora y fecha", "hora y fecha", "hora_y_fecha")), None)
    col_global = next((c for c in df.columns if c.lower() in ("resultado global", "resultado_global")), None)

    if not (col_nombre and col_ts and col_global):
        raise ValueError(
            f"Columnas requeridas no encontradas. Presentes: {list(df.columns)}. "
            "Se requieren: 'Nombre', 'Hora y Fecha', 'Resultado Global'."
        )

    # Coaccionar Resultado Global a entero y filtrar no-cero
    def to_int_safe(x: Any) -> int:
        try:
            return int(str(x).strip())
        except Exception:
            return 0

    df["_ResultadoGlobal"] = df[col_global].apply(to_int_safe)
    df["_TS_norm"] = df[col_ts].apply(normalize_timestamp)
    df["_Nombre_tokens"] = df[col_nombre].apply(tokenize_name)

    df = df[df["_ResultadoGlobal"] != 0].copy()
    if df.empty:
        print("No hay filas con 'Resultado Global' distinto de 0.")
    
    # Leer JSON y agrupar por timestamp normalizado
    items = load_json_records(json_path)
    by_ts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for it in items:
        data = it.get("data", {}) or {}
        ts = normalize_timestamp(data.get("timestamp", ""))
        by_ts[ts].append(it)

    rows_out: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        excel_name_tokens = row["_Nombre_tokens"]
        excel_ts = row["_TS_norm"]
        excel_global = row["_ResultadoGlobal"]

        candidates = by_ts.get(excel_ts, [])
        if not candidates:
            # No hay JSON con ese timestamp; se omite
            continue

        for it in candidates:
            data = it.get("data", {}) or {}
            total_hits = data.get("total_hits", 0)
            try:
                total_hits = int(total_hits)
            except Exception:
                total_hits = 0

            # Debe coincidir exactamente con Resultado Global
            if total_hits != excel_global:
                continue

            # Validar found_records
            frs = data.get("found_records", []) or []
            for rec in frs:
                # Elegir el nombre del registro para comparar (preferimos 'name')
                rec_name = rec.get("name") or rec.get("full_name") or ""
                rec_tokens = tokenize_name(rec_name)

                # Debe coincidir exactamente la cantidad y contenido de palabras (ignorando orden y acentos)
                if not tokens_equal(excel_name_tokens, rec_tokens):
                    continue

                institution = rec.get("institution")
                description = rec.get("description")
                links = rec.get("links")
                other_information = rec.get("other_information")

                # También útil incluir algunos campos del registro
                source_type = rec.get("source_type") or data.get("source_type") or ""
                gender = rec.get("gender", "")

                # 'found_data' combinado como texto
                parts = []
                if institution:
                    parts.append(f"{bulletify(institution)}")
                if description:
                    parts.append(f"{bulletify(description)}")
                if links:
                    parts.append(f"{bulletify(links)}")
                if other_information:
                    parts.append(f"{bulletify(other_information)}")
                found_data_text = " - ".join(parts) if parts else ""

                rows_out.append({
                    "Nombre": row[col_nombre],
                    "Timestamp": excel_ts,  # timestamp normalizado
                    "Hits": total_hits,
                    "Original Hits": excel_global,
                    "Item": it.get("item", ""),
                    "Record Name": rec_name,
                    "Source Type": source_type,
                    "Gender": gender,
                    "Institution": bulletify(institution),
                    "Description": bulletify(description),
                    "Links": bulletify(links),
                    "Other Information": bulletify(other_information),
                    "found_data": found_data_text,
                })

    # Crear DataFrame de salida
    if rows_out:
        out_df = pd.DataFrame(rows_out)
        # Orden sugerido de columnas
        col_order = [
            "Nombre", "Timestamp", "Hits", "Original Hits", "Item", "Record Name", "Source Type", "Gender",
            "Institution", "Description", "Links", "Other Information", "found_data"
        ]
        # Conservar orden cuando existan
        col_order = [c for c in col_order if c in out_df.columns] + [c for c in out_df.columns if c not in col_order]
        out_df = out_df[col_order]
    else:
        # dataframe vacío pero con columnas esperadas
        out_df = pd.DataFrame(columns=[
            "Nombre", "Timestamp", "Hits", "Original Hits", "Item", "Record Name", "Source Type", "Gender",
            "Institution", "Description", "Links", "Other Information", "found_data"
        ])

    # Guardar Excel
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False, sheet_name="matches")

    print(f"Listo. Filas coincidentes: {len(out_df)}. Archivo generado en: {out_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compara Excel vs JSON por timestamp, total_hits y nombre.")
    p.add_argument("--excel", required=True, help="Ruta al archivo Excel de entrada (xlsx/xls).")
    p.add_argument("--json", required=True, help="Ruta al archivo JSON de entrada.")
    p.add_argument("--out", default="salida_matches.xlsx", help="Ruta del Excel de salida.")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(Path(args.excel), Path(args.json), Path(args.out))
