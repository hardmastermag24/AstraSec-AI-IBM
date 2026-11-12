import pytest
from tools.resumir_validacion import summarize


def row(**changes):
    result = dict(participante_id='U01', tarea='T1', version='test', fecha='2026-10-25',
                  resultado='completo', tiempo_segundos='30', ayudas='0')
    result.update(changes)
    return result


def test_empty_is_pending_not_failure_or_success():
    result = summarize([])
    assert result['estado'] == 'pendiente'
    assert result['exito_sin_ayuda_porcentaje'] is None


def test_only_complete_without_help_counts_as_independent_success():
    result = summarize([row(), row(tarea='T2', ayudas='1'), row(tarea='T3', resultado='parcial')])
    assert result['exitos_sin_ayuda'] == 1
    assert result['exito_sin_ayuda_porcentaje'] == 33.33


@pytest.mark.parametrize('value', ['nan', 'inf', '-1'])
def test_invalid_times_are_rejected(value):
    with pytest.raises(ValueError):
        summarize([row(tiempo_segundos=value)])


def test_duplicate_task_is_rejected():
    with pytest.raises(ValueError):
        summarize([row(), row()])


def test_incomplete_rows_cannot_become_evidence():
    with pytest.raises(ValueError):
        summarize([row(participante_id='')])
