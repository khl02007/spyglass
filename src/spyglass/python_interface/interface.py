from typing import List

from spyglass.common import Session, Raw, Electrode


class SpyGlassSession:
    def __init__(self, nwb_file: str):
        self.nwb_file = nwb_file
        self.key = Session & {"nwb_file_name": self.nwb_file}.fetch1()
        self.electrodes = SpyGlassElectrode(self.nwb_file)
        self.raw = Raw & {"nwb_file_name": self.nwb_file}
        self.spikesorting = SpyGlassSpikeSorting(self.nwb_file)

    def __repr__(self):
        return Session & {"nwb_file_name": self.nwb_file}

    def to_dict(self):
        return self.key

    def run_spikesorting(
        sort_group_name: str,
        sort_group_electrodes,
        sort_interval_name: str,
        sort_interval: List,
        preprocessing_param,
        sorter_param,
        sort_group_ref_electrode=None,
    ):
        return None


class SpyGlassElectrode:
    def __init__(self, nwb_file):
        self.nwb_file = nwb_file
        self.key = Electrode & {"nwb_file_name": self.nwb_file}.fetch()

    def __repr__(self):
        return Electrode & {"nwb_file_name": self.nwb_file}

    def to_dict(self):
        return self.key


class SpyGlassSpikeSorting:
    def __init__(self) -> None:
        pass
