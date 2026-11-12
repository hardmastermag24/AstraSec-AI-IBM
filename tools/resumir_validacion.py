"""Summarize observed sessions only; empty templates remain pending."""
import argparse
import csv
import json
import math
import statistics
from pathlib import Path


def summarize(rows):
    observed = []
    seen = set()
    for row in rows:
        if not any(str(v or '').strip() for v in row.values()):
            continue
        participant = row.get('participante_id', '').strip()
        task = row.get('tarea', '').strip()
        version = row.get('version', '').strip()
        date = row.get('fecha', '').strip()
        outcome = row.get('resultado', '').strip().lower()
        if not participant or not task or not version or not date or outcome not in {'completo', 'parcial', 'fallo'}:
            raise ValueError('Fila incompleta: participante, tarea, versión, fecha y resultado son obligatorios.')
        key = (participant, version, date, task)
        if key in seen:
            raise ValueError('Tarea duplicada en la misma sesión.')
        seen.add(key)
        seconds = float(row.get('tiempo_segundos', ''))
        help_count = int(row.get('ayudas', ''))
        if not math.isfinite(seconds) or seconds < 0 or help_count < 0:
            raise ValueError('Tiempo y ayudas deben ser valores válidos no negativos.')
        observed.append((participant, seconds, outcome, help_count))
    if not observed:
        return {'estado': 'pendiente', 'participantes': 0, 'tareas_observadas': 0,
                'exito_sin_ayuda_porcentaje': None, 'mediana_tiempo_observado_segundos': None}
    success = sum(outcome == 'completo' and help_count == 0 for _, _, outcome, help_count in observed)
    return {'estado': 'observaciones_registradas_no_certificacion',
            'participantes': len({row[0] for row in observed}), 'tareas_observadas': len(observed),
            'exitos_sin_ayuda': success, 'exito_sin_ayuda_porcentaje': round(success / len(observed) * 100, 2),
            'mediana_tiempo_observado_segundos': statistics.median(row[1] for row in observed),
            'limite': 'Estadística descriptiva; no prueba ahorro, ROI ni representatividad.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_path', type=Path)
    args = parser.parse_args()
    with args.csv_path.open(encoding='utf-8-sig', newline='') as stream:
        result = summarize(csv.DictReader(stream))
    print(json.dumps(result, ensure_ascii=False, indent=2))
