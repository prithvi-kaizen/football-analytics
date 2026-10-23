"""Build a checksum-verified byte index and redistributable real-data fixture.

Run only after acquiring the original full J03WPY match. This is a release tool,
not required for downloading the small sample or running the application.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rest_defence.data import ROOT, digest, source_files


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tracking", type=Path)
    parser.add_argument("--seconds", type=int, default=180)
    args = parser.parse_args()
    entry = source_files("J03WPY")["tracking"]
    if digest(args.tracking, "md5") != entry["computed_md5"]:
        raise ValueError("Original source MD5 mismatch")
    prefix = '<PutDataRequest><Positions>\n'
    suffix = '</Positions></PutDataRequest>\n'
    spans, header, start, end, chunks = [], None, None, None, []
    # All native first-half series begin at N=10000 in this pinned match.
    lower, upper = 10000, 10000 + args.seconds * 25
    def finish():
        if chunks:
            payload = b"".join(chunks)
            spans.append(dict(header=header, start=start, end=end,
                              sha256=hashlib.sha256(payload).hexdigest()))
    with args.tracking.open("rb") as f:
        while True:
            offset = f.tell()
            line = f.readline()
            if not line:
                break
            if line.startswith(b"<FrameSet "):
                finish()
                header, start, end, chunks = line.decode(), None, None, []
                attributes = ET.fromstring(line.strip()[:-1] + b"/>").attrib
            elif line.startswith(b"<Frame ") and attributes["GameSection"] == "firstHalf":
                n = int(ET.fromstring(line).attrib["N"])
                if lower <= n <= upper:
                    if start is None:
                        start = offset
                    end = offset + len(line) - 1
                    chunks.append(line)
        finish()
    sample = bytearray(prefix.encode())
    with args.tracking.open("rb") as f:
        for span in spans:
            f.seek(span["start"])
            sample.extend(span["header"].encode())
            sample.extend(f.read(span["end"] - span["start"] + 1))
            sample.extend(b"</FrameSet>\n")
    sample.extend(suffix.encode())
    index = dict(url=entry["download_url"], source_size=entry["size"], source_md5=entry["computed_md5"],
                 prefix=prefix, suffix=suffix, ranges=spans, first_frame=lower, last_frame=upper,
                 sample_sha256=hashlib.sha256(sample).hexdigest(), seconds=args.seconds,
                 total_range_bytes=sum(s["end"]-s["start"]+1 for s in spans))
    (ROOT / "docs/source/sample-ranges.json").write_text(json.dumps(index, indent=2))
    sample_dir = ROOT / "data/sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    manifest = dict(source="DFL; Bassek et al. (2025), doi:10.1038/s41597-025-04505-y", license="CC BY 4.0", files={})
    for key in ["tracking", "meta", "events"]:
        payload = bytes(sample) if key == "tracking" else (ROOT / f"data/raw/J03WPY_{key}.xml").read_bytes()
        compressed = gzip.compress(payload, mtime=0)
        (sample_dir / f"{key}.xml.gz").write_bytes(compressed)
        manifest["files"][key] = dict(gzip_sha256=hashlib.sha256(compressed).hexdigest(), xml_sha256=hashlib.sha256(payload).hexdigest())
    (sample_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(dict(entities=len(spans), download_bytes=index["total_range_bytes"],
                          compressed_bytes=(sample_dir / "tracking.xml.gz").stat().st_size)))


if __name__ == "__main__":
    main()
