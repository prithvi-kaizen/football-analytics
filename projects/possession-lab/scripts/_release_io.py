"""Integrity-checked restoration of reviewed, regular-file-only project archives."""
import hashlib
import tarfile
from pathlib import Path, PurePosixPath


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def restore(archive, manifest, output):
    archive, output = Path(archive), Path(output)
    if sha256(archive) != manifest['archive_sha256']:
        raise ValueError('Archive checksum mismatch')
    expected = manifest['files']
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError('Archive members differ from the reviewed manifest')
        for member in members:
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or '\\' in member.name:
                raise ValueError('Unsafe archive member')
            destination = output / member.name
            if not destination.resolve().is_relative_to(output.resolve()):
                raise ValueError('Archive member escapes the output directory')
            content = bundle.extractfile(member).read()
            if hashlib.sha256(content).hexdigest() != expected[member.name]:
                raise ValueError('Archive member checksum mismatch: ' + member.name)
            if destination.exists() and sha256(destination) != expected[member.name]:
                raise ValueError('Refusing to overwrite a changed local file: ' + str(destination))
        # Validate every member before writing any destination.
        for member in members:
            destination = output / member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(bundle.extractfile(member).read())
    return len(members)
