import hashlib
import json

import pytest

from tacticai_lite.data import DataError, REVISION, Store, unique_records


def test_cache_integrity_and_offline(tmp_path):
    p=tmp_path/'events.json';payload=b'[{"id":"a"}]';p.write_bytes(payload)
    with pytest.raises(DataError,match='Unverified'): Store(tmp_path,True).get('events.json')
    p.with_suffix('.receipt.json').write_text(json.dumps({'revision':REVISION,'sha256':hashlib.sha256(payload).hexdigest()}))
    assert Store(tmp_path,True).get('events.json')==[{'id':'a'}]
    p.write_bytes(b'[]')
    with pytest.raises(DataError,match='integrity'): Store(tmp_path,True).get('events.json')
    with pytest.raises(FileNotFoundError): Store(tmp_path,True).get('absent.json',optional=True)


def test_duplicate_ids():
    with pytest.raises(DataError): unique_records([{'id':'a'},{'id':'a'}],'id')


def test_optional_360_404_is_cached_for_offline_replay(tmp_path,monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr('tacticai_lite.data.requests.get',lambda *a,**k:SimpleNamespace(status_code=404))
    assert Store(tmp_path).get('data/three-sixty/1.json',optional=True) is None
    assert Store(tmp_path,True).get('data/three-sixty/1.json',optional=True) is None
    with pytest.raises(FileNotFoundError): Store(tmp_path,True).get('data/three-sixty/1.json')
