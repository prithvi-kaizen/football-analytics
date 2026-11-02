"""Publication checks do not change research models or historical test expectations."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('publication_release_io', ROOT / 'scripts/_release_io.py')
release_io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_io)


def fixture_archive(tmp_path, name='reviewed.txt'):
    path = tmp_path / 'bundle.tar.gz'
    content = b'reviewed content\n'
    with tarfile.open(path, 'w:gz') as archive:
        info = tarfile.TarInfo(name)
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))
    manifest = {'archive_sha256': release_io.sha256(path),
                'files': {name: hashlib.sha256(content).hexdigest()}}
    return path, manifest, content


def test_reviewed_archive_restores_exact_bytes_and_is_idempotent(tmp_path):
    path, manifest, content = fixture_archive(tmp_path)
    output = tmp_path / 'output'
    assert release_io.restore(path, manifest, output) == 1
    assert (output / 'reviewed.txt').read_bytes() == content
    assert release_io.restore(path, manifest, output) == 1


def test_tampered_archive_is_rejected_before_writing(tmp_path):
    path, manifest, _ = fixture_archive(tmp_path)
    path.write_bytes(path.read_bytes() + b'changed')
    with pytest.raises(ValueError, match='checksum'):
        release_io.restore(path, manifest, tmp_path / 'output')
    assert not (tmp_path / 'output').exists()


def test_parent_path_is_rejected_even_with_matching_hash(tmp_path):
    path, manifest, _ = fixture_archive(tmp_path, '../escape.txt')
    with pytest.raises(ValueError, match='Unsafe'):
        release_io.restore(path, manifest, tmp_path / 'output')
    assert not (tmp_path / 'escape.txt').exists()


def test_changed_local_result_is_preserved(tmp_path):
    path, manifest, _ = fixture_archive(tmp_path)
    output = tmp_path / 'output'
    output.mkdir()
    (output / 'reviewed.txt').write_text('local experiment')
    with pytest.raises(ValueError, match='Refusing'):
        release_io.restore(path, manifest, output)
    assert (output / 'reviewed.txt').read_text() == 'local experiment'


def test_public_release_has_no_accuracy_for_real_samples(tmp_path):
    manifest = json.loads((ROOT / 'web/release.json').read_text())
    release_io.restore(ROOT / 'web/release.tar.gz', manifest, tmp_path / 'website')
    for name in ('public1', 'public2'):
        data = json.loads((tmp_path / 'website/data' / f'{name}.json').read_text())
        assert data['truth'] is None
        assert all(model['metrics'] is None for model in data['models'])
    assert (tmp_path / 'website/runtime/PYODIDE-LICENSE.txt').is_file()
    assert not any('.openai' in name or 'public_sanity' in name for name in manifest['files'])
