"""Failure recovery and run boundaries, using invented timeline data only."""
import json
import sqlite3

import pytest

from mueser.timeline import case_paths
from mueser.timeline.db import build_db
from test_timeline import _synthetic_case


def test_failed_rebuild_preserves_last_database_and_json(tmp_path):
    case = _synthetic_case(tmp_path)
    paths = case_paths(case)
    run = paths['runs'] / 'collect-synthetic-01'
    proposals = paths['proposals'] / 'connect-synthetic-01'
    build_db(case, run, proposals, echo=lambda _: None)
    before = {name: paths[name].read_bytes() for name in ('db', 'json')}
    nodes = json.loads((run / 'nodes.json').read_text())
    (run / 'nodes.json').write_text(json.dumps(nodes + [nodes[0]]))
    with pytest.raises(sqlite3.IntegrityError):
        build_db(case, run, proposals, echo=lambda _: None)
    assert {name: paths[name].read_bytes() for name in before} == before
    with sqlite3.connect(paths['db']) as connection:
        assert connection.execute('SELECT COUNT(*) FROM nodes').fetchone()[0] == 4
    assert not list(paths['timeline'].glob('.build-*'))


def test_proposal_for_person_outside_selected_collect_run_is_not_an_edge(tmp_path):
    case = _synthetic_case(tmp_path)
    paths = case_paths(case)
    run = paths['runs'] / 'collect-synthetic-01'
    proposals = paths['proposals'] / 'connect-synthetic-01'
    path = proposals / 'proposals.json'
    results = json.loads(path.read_text())
    results[0]['person'] = 'Q-not-in-this-collect-run'
    path.write_text(json.dumps(results))
    _, output = build_db(case, run, proposals, echo=lambda _: None)
    data = json.loads(output.read_text())
    ids = {node['id'] for node in data['nodes']}
    assert all(edge['src'] in ids and edge['dst'] in ids for edge in data['edges'])
