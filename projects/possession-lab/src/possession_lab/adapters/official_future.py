class OfficialAdapter:
    """Reserved integration seam. No restricted paths, loaders or data are opened in this lab.

    A human-run implementation outside Codex must provide TrackingAdapter.load(), map ATD
    frame_id - 1, explicitly assign teams and periods, scale unit coordinates to metres, and
    optionally fuse uncertain Smart Tagging as evidence. See docs/SECURITY.md.
    """

    def load(self):
        raise RuntimeError("Restricted competition ingestion is disabled in the preparation lab")
