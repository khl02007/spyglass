from typing import Union, Sequence, Type, Dict
import numpy as np

from spyglass.common import Session, Raw, Electrode
from spyglass.spikesorting import SortGroup, SpikeSorting

class SpyGlassSession:
    def __init__(self, nwb_file: str):
        self.nwb_file = nwb_file
        self.nwb_file_ = add_underscore_before_extension(nwb_file)
        self.key = Session & {"nwb_file_name": self.nwb_file}.fetch1()
        self.electrodes = SpyGlassElectrode(self.nwb_file)
        self.raw = Raw & {"nwb_file_name": self.nwb_file}
        self.spikesorting = SpyGlassSpikeSorting(self.nwb_file)

    def __repr__(self):
        return Session & {"nwb_file_name": self.nwb_file}

    def to_dict(self):
        return self.key

    def run_spikesorting(self, version, **kwargs):
        if version == 'v1':
            self._run_spike_sorting_version1(**kwargs)
        elif version == 'v2':
            self._run_spike_sorting_version2(**kwargs)
        else:
            # Handle invalid first argument
            raise ValueError(f"Invalid version identifier: {version}")


    def _run_spikesorting_version1(
        self,
        version: str,
        sort_group_id: int,
        sort_group_electrodes: Union[Union[Sequence[float], np.ndarray], None],
        sort_interval_name: str,
        sort_interval: Union[Sequence[float], np.ndarray],
        preprocessing_param: Dict,
        sorter_param: Dict,
        sort_group_ref_electrode: Union[int, None]=None,
    ) -> Type[SpyGlassSpikeSorting]:
        """Run spike sorting

        Parameters
        ----------
        version : str
            The version number of the spike sorting pipeline
        sort_group_id : int
            _description_
        sort_group_electrodes : Union[Union[Sequence[float], np.ndarray], None]
            _description_
        sort_interval_name : str
            _description_
        sort_interval : Union[Sequence[float], np.ndarray]
            _description_
        preprocessing_param : Dict
            _description_
        sorter_param : Dict
            _description_
        sort_group_ref_electrode : Union[int, None], optional
            _description_, by default None

        Returns
        -------
        _type_
            _description_
        """
        if sort_group_ref_electrode is None:
            sort_group_ref_electrode = -1
        SortGroup.insert1([self.nwb_file_, sort_group_id, sort_group_ref_electrode])

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
    def __init__(self, version) -> None:
        self.version=version
    def __repr__(self):
        return SpikeSorting & {"nwb_file_name": self.nwb_file}



def add_underscore_before_extension(file_name: str) -> str:
    """Adds an underscore before the file extension"""
    parts = file_name.split('.')
    if len(parts) > 1:
        parts[-2] = parts[-2] + '_'
        return '.'.join(parts)
    else:
        return file_name

def get_spikesorting_param(version: str):
    if version=="v1":
        return {}
    elif version=="v2":
        return {}
    else:
        raise ValueError(f"Invalid version identifier: {version}")
