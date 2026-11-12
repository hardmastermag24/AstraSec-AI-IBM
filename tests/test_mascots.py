"""Activity indicators must reflect outcomes and safely display file names."""
import base64
import re
from types import SimpleNamespace

import pytest
from app.core import mascots


def test_activity_tracks_progress_until_completion(monkeypatch):
    events = []
    monkeypatch.setattr(mascots, 'update_activity', lambda *args: events.append(args))
    with mascots.agent_activity('scanner', 'Leyendo') as update:
        update('archivo.txt', .5)
    assert [entry[1] for entry in events] == ['busy', 'busy', 'done']
    assert events[1][-1] == .5


def test_failure_is_not_reported_as_completed(monkeypatch):
    events = []
    monkeypatch.setattr(mascots, 'update_activity', lambda *args: events.append(args[1]))
    with pytest.raises(ValueError, match='failed'):
        with mascots.agent_activity('advisor', 'Consulta'):
            raise ValueError('failed')
    assert events == ['busy', 'error']


def test_file_names_are_escaped_and_progress_is_bounded(monkeypatch):
    monkeypatch.setattr(mascots, 'st', SimpleNamespace(session_state={}))
    html = mascots._panel('scanner', 'busy', '<script>bad</script>', '<b>file.txt</b>', 2)
    assert '<script>bad</script>' not in html
    assert '&lt;b&gt;file.txt&lt;/b&gt;' in html
    assert 'aria-valuenow="100"' in html


def test_animation_setting_is_included_in_the_svg_image(monkeypatch):
    monkeypatch.setattr(mascots, 'st', SimpleNamespace(session_state={'animate_mascots': False}))
    image = mascots.mascot_image('scanner', 'busy')
    svg = base64.b64decode(re.search(r'base64,([^\"]+)', image)[1]).decode()
    assert 'class="astra-mascots am-busy"' in svg
    assert 'prefers-reduced-motion:reduce' in svg
    assert '<script' not in svg


def test_hidden_companion_creates_no_ui(monkeypatch):
    monkeypatch.setattr(mascots, 'st', SimpleNamespace(session_state={'show_mascots': False}))
    mascots.update_activity('scanner', 'busy', 'Leyendo')
