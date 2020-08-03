import os
import datajoint as dj
import pynwb
from .dj_helper_fn import dj_replace, fetch_nwb

schema = dj.schema("common_lab", locals())

import kachery as ka

# define the fields that should be kept in AnalysisNWBFiles
nwb_keep_fields = ('devices', 'electrode_groups', 'electrodes', 'experiment_description', 'experimenter', 
                   'file_create_date', 'identifier', 'intervals', 'institution', 'lab', 'session_description', 'session_id', 
                   'session_start_time', 'subject', 'timestamps_reference_time')

# TODO: make decision about docstring -- probably use :param ...:

@schema
class Nwbfile(dj.Manual):
    definition = """
    nwb_file_name: varchar(255) #the name of the NWB file
    ---
    nwb_file_abs_path: varchar(255) # the full path name to the file
    nwb_file_sha1: varchar(40) # the sha1 hash of the NWB file for kachery
    """
    def insert_from_relative_file_name(self, nwb_file_name):
        """Insert a new session from an existing nwb file.

        Args:
            nwb_file_name (str): Relative path to the nwb file
        """
        nwb_file_abs_path = Nwbfile.get_abs_path(nwb_file_name)
        assert os.path.exists(nwb_file_abs_path), f'File does not exist: {nwb_file_abs_path}'

        print('Computing SHA-1 and storing in kachery...')
        with ka.config(use_hard_links=True):
            kachery_path = ka.store_file(nwb_file_abs_path)
            sha1 = ka.get_file_hash(kachery_path)
        
        self.insert1(dict(
            nwb_file_name=nwb_file_name,
            nwb_file_abs_path=nwb_file_abs_path,
            nwb_file_sha1=sha1
        ), skip_duplicates=True)
    
    @staticmethod
    def get_abs_path(nwb_file_name):
        base_dir = os.getenv('NWB_DATAJOINT_BASE_DIR', None)
        assert base_dir is not None, 'You must set NWB_DATAJOINT_BASE_DIR or provide the base_dir argument'

        nwb_file_abspath = os.path.join(base_dir, nwb_file_name)
        return nwb_file_abspath

@schema
class AnalysisNwbfile(dj.Manual):
    definition = """   
    analysis_file_name: varchar(255) # the name of the file 
    ---
    -> Nwbfile # the name of the parent NWB file. Used for naming and metadata copy
    analysis_file_abs_path: varchar(255) # the full path of the file
    analysis_file_description='': varchar(255) # an optional description of this analysis
    analysis_file_sha1='': varchar(40) # the sha1 hash of the NWB file for kachery
    analysis_parameters=NULL: blob # additional relevant parmeters. Currently used only for analyses that span multiple NWB files
    """

    def __init__(self, *args):
        # do your custom stuff here
        super().__init__(*args)  # call the base implementation


    def create(self, nwb_file_name):
        '''
        Opens the input NWB file, creates a copy, writes out the copy to disk and return the name of the new file
        :param nwb_file_name: str
        :return: analysis_file_name: str
        '''
        #
        nwb_file_abspath = Nwbfile.get_abs_path(nwb_file_name)

        io  = pynwb.NWBHDF5IO(path=nwb_file_abspath, mode='r')
        nwbf = io.read()
        
        #  pop off the unnecessary elements to save space

        nwb_fields = nwbf.fields
        for field in nwb_fields:
            if field not in nwb_keep_fields:
                nwb_object = getattr(nwbf, field)
                if type(nwb_object) is pynwb.core.LabelledDict:  
                    for module in list(nwb_object.keys()):
                        mod = nwb_object.pop(module)
                        nwbf._remove_child(mod)
        
                        
        key = dict()
        key['nwb_file_name'] = nwb_file_name
        # get the current number of analysis files related to this nwb file
        n_analysis_files = len((AnalysisNwbfile() & {'parent_nwb_file': nwb_file_name}).fetch())
        # name the file, adding the number of files with preceeding zeros

        analysis_file_name = os.path.splitext(nwb_file_name)[0] + '_' + str(n_analysis_files).zfill(8) + '.nwb'
        key['analysis_file_name'] = analysis_file_name
        key['analysis_file_description'] = ''
        # write the new file
        print(f'writing new NWB file {analysis_file_name}')
        analysis_file_abs_path = AnalysisNwbfile.get_abs_path(analysis_file_name)
        key['analysis_file_abs_path'] = analysis_file_abs_path
        # export the new NWB file
        with pynwb.NWBHDF5IO(path=analysis_file_abs_path, mode='w') as export_io:
            export_io.export(io, nwbf)

        io.close()

        # insert the new file
        self.insert1(key)
        return analysis_file_name

    def add_to_kachery(self, analysis_file_name): 
        """Add the specified analysis nwb file to the Kachery store for sharing
        :return: none
        :rtype: none
        """
        print('Computing SHA-1 and storing in kachery...')
        analysis_file_info  = (AnalysisNwbfile() & {'analysis_file_name' : analysis_file_name}).fetch1()
        
        with ka.config(use_hard_links=True):
            kachery_path = ka.store_file(analysis_file_info['analysis_file_abs_path'])
            sha1 = ka.get_file_hash(kachery_path)
        #update the entry for this element with the sha1 entry
        
        new_sha1 = (analysis_file_name, sha1)
        self.insert(dj_replace(analysis_file_info, new_sha1, 'analysis_file_name', 'analysis_file_sha1'),
                                 replace="True")

    @staticmethod
    def get_abs_path(analysis_nwb_file_name):
        base_dir = os.getenv('NWB_DATAJOINT_BASE_DIR', None)
        assert base_dir is not None, 'You must set NWB_DATAJOINT_BASE_DIR or provide the base_dir argument'

        analysis_nwb_file_abspath = os.path.join(base_dir, 'analysis', analysis_nwb_file_name)
        return analysis_nwb_file_abspath