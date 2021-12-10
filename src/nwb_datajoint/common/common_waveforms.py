import os
from pathlib import Path

import datajoint as dj
import pynwb
import sortingview as sv
import spikeinterface as si

from .common_nwbfile import AnalysisNwbfile
from .common_spikesorting import (SpikeSorting, SpikeSortingRecording, SortingID)

si.set_global_tmp_folder(os.environ['KACHERY_TEMP_DIR'])

schema = dj.schema('common_waveforms')

@schema
class WaveformParameters(dj.Manual):
    definition = """
    list_name: varchar(80) # name of waveform extraction parameters
    ---
    params: blob # a dict of waveform extraction parameters
    """
    def insert_default_params(self):
        key = {}
        key['list_name'] = 'default'
        key['params'] = {'ms_before':1, 'ms_after':1, 'max_spikes_per_unit':1000}
        self.insert1(key) 

@schema
class WaveformSelection(dj.Manual):
    definition = """
    -> SpikeSorting
    -> WaveformParameters
    ---
    """

@schema
class Waveforms(dj.Computed):
    definition = """
    -> WaveformSelection
    ---
    -> AnalysisNwbfile
    waveform_extractor_path: varchar(220)
    """
    def make(self, key):
        recording_object = (SpikeSortingRecording & key).fetch1('recording_extractor_object')
        recording = sv.LabboxEphysRecordingExtractor(recording_object)
        
        sorting_object = (SortingID & key).fetch1('sorting_extractor_object')
        sorting = sv.LabboxEphysSortingExtractor(sorting_object)

        waveform_extractor_name =  self._get_waveform_extractor_name(key)
        key['analysis_file_name'] = waveform_extractor_name + '.nwb'
        AnalysisNwbfile().add(key['nwb_file_name'], key['analysis_file_name'])
        
        key['waveform_extractor_path'] = self._get_waveform_save_path(waveform_extractor_name)
        
        si.extract_waveforms(recording=recording, 
                             sorting=sorting, 
                             folder=key['waveform_extractor_path'],
                             **key['params'])
        
        self.insert1(key)

        # TODO: save waveforms as nwb file
        # The following is a rough sketch
        # analysis_file_name = AnalysisNwbfile().create(key['nwb_file_name'])
        # or
        # nwbfile = pynwb.NWBFile(...)
        # wfs = [
        #         [     # elec 1
        #             [1, 2, 3],  # spike 1, [sample 1, sample 2, sample 3]
        #             [1, 2, 3],  # spike 2
        #             [1, 2, 3],  # spike 3
        #             [1, 2, 3]   # spike 4
        #         ], [  # elec 2
        #             [1, 2, 3],  # spike 1
        #             [1, 2, 3],  # spike 2
        #             [1, 2, 3],  # spike 3
        #             [1, 2, 3]   # spike 4
        #         ], [  # elec 3
        #             [1, 2, 3],  # spike 1
        #             [1, 2, 3],  # spike 2
        #             [1, 2, 3],  # spike 3
        #             [1, 2, 3]   # spike 4
        #         ]
        # ]
        # elecs = ... # DynamicTableRegion referring to three electrodes (rows) of the electrodes table
        # nwbfile.add_unit(spike_times=[1, 2, 3], electrodes=elecs, waveforms=wfs)
        
        # key['analysis_nwb_file'] = analysis_nwb_file_path
    
    def load_waveforms(self, key):
        # TODO: check if multiple entries are passed
        folder = key['waveform_extractor_path']
        we = si.WaveformExtractor.load_from_folder(folder)
        return we
    
    def fetch_nwb(self, key):
        return NotImplementedError
    
    def _get_waveform_extractor_name(self, key):
        sorting_name = SpikeSorting().get_sorting_name(key)
        we_name = sorting_name + '_waveform'
        return we_name

    def _get_waveform_save_path(self, waveform_extractor_name):
        waveforms_dir = Path(os.environ['NWB_DATAJOINT_BASE_DIR']) / 'waveforms' / waveform_extractor_name
        if (waveforms_dir).exists() is False:
            os.mkdir(waveforms_dir)
        return str(waveforms_dir)