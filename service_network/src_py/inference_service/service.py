import os
import time
import uuid
import json
import numpy as np
import trimesh
from pathlib import Path

from .file_inference import FileInference

# Bounds for our normalized dataset
BOUNDS = np.array([[-3.105525016784668, -1.7949625253677368, -0.330342], [6.356535, 1.7951075, 2.317086]])
HALF_SIZE = 0.5 * (BOUNDS[1] - BOUNDS[0])
POSITION = 0.5 * (BOUNDS[1] + BOUNDS[0])

NUM_SAMPLE_POINTS = 1_255_000


class Service:
    data = None         # loaded / received data
    extension = ""
    config_request_old = {}
    file_inferences = {}
    uploaded_files_dir = None
    current_stl_path = None
    current_streamlines_path = None

    def __init__(self,
                 files=[],
                 field_names=[],
                 unnormalize=False,
                 preload=True,
                 prune_points=0,
                 num_points=NUM_SAMPLE_POINTS,
                 uploaded_files_dir=None):
        self.field_names = field_names
        self.unnormalize_data = unnormalize
        self.preload_data = preload
        self.prune_points = prune_points
        self.num_sample_points = num_points
        self.uploaded_files_dir = uploaded_files_dir or os.environ.get("UPLOAD_FILES_DIR", "/app/uploaded_files")

        self._reset_config()

        if len(files) > 0:
            self.from_file = files['from']
            self.to_file = files['to']

            for i in range(self.from_file, self.to_file + 1):
                filepath = FileInference.get_filepath(files, i)
                self.file_inferences[i] = FileInference(filepath)

    def _reset_config(self):
        self.config_request_old['id'] = -1
        self.config_request_old['config'] = -1
        self.config_request_old['multip'] = -1
        # self.config_request_old['params'] = ""    # not used

    def _field_names_reader(self):
        '''Get list of fields in the data dictionary'''

        if self.file_inferences:
            # load fields from a first file
            first_key = next(iter(self.file_inferences))
            self.field_names = self.file_inferences[first_key].get_field_names()
        else:
            if len(self.field_names) == 0:
                raise RuntimeError("No field names set")

        self.field_names.append('sdf_bounds')

        print(f"Data fields: {self.field_names}")

    def _get_data_from_file(self, config_request):

        file_index = int(config_request['id'])
        file_index = int(np.clip(file_index, self.from_file, self.to_file))

        if file_index not in self.file_inferences:
            print(f"ERROR: Requested file with index {file_index} not found!")
            return -1

        if not self.preload_data:
            self.file_inferences[file_index].load_data()

        if self.file_inferences and file_index in self.file_inferences:
            self.data = self.file_inferences[file_index].get_data()

        return file_index

    def _get_data_from_script(self, config_request):
        """Load data from uploaded files instead of running Triton inference"""

        if config_request == self.config_request_old:
            return

        # config_request['id'] now contains the filename (not an integer ID)
        # config_request['streamlines'] contains the streamlines JSON filename
        stl_filename = config_request.get('id', 'default.stl')
        streamlines_filename = config_request.get('streamlines', 'streamlines.json')

        self.config_request_old = config_request

        print(f"Loading uploaded files: STL={stl_filename}, Streamlines={streamlines_filename}")

        # Load uploaded files
        uploaded_data = self.load_uploaded_files(stl_filename, streamlines_filename)

        if uploaded_data:
            self.data = uploaded_data
            print("Successfully loaded uploaded files")
        else:
            print("WARNING: Failed to load uploaded files, using empty data")
            self.data = {}

    @staticmethod
    def prune_point_count(array, field_name):

        print(f"WARNING: Pruning '{field_name}' data! (array.shape={array.shape}, dtype={array.dtype})")

        rng = np.random.default_rng(0)
        levels = np.arange(1024)
        rng.shuffle(levels)
        threshold = int(1024 * (2097152 / array.shape[0]))
        pred = np.less_equal(levels, threshold)
        pred = np.tile(pred, int(array.shape[0] / 1024))
        array = np.compress(pred, array, axis=0)

        print(f"WARNING: Pruned '{field_name}' data! (array.shape={array.shape}, dtype={array.dtype})")

        return array

    def _get_array(self, field_name):
        '''Get numpy array weith specified field name, normalize and compute sdf bounds'''

        if not self.data:
            print(f"ERROR: Data for '{field_name}' does not exist")
            return None

        # This is needed by Flow voxelization
        if field_name == 'sdf_bounds':
            if 'sdf' in self.data:
                p_sdf = self.data.get('sdf')
            else:
                print("ERROR: Could not get 'sdf_bounds', 'sdf' array not found")
                return None

            if 'bounding_box_dims' in self.data:
                bounds = self.data.get('bounding_box_dims')
                halfsize = 0.5 * (bounds[1] - bounds[0])
                position = 0.5 * (bounds[1] + bounds[0])
            else:
                halfsize = HALF_SIZE
                position = POSITION

            sdf_grid_size = p_sdf.shape - np.array([1, 1, 1])
            sdf_cell_size = 2.0 * halfsize / (sdf_grid_size)

            array = 100 * np.array([position - halfsize - 0.5 * sdf_cell_size, position + halfsize + 0.5 * sdf_cell_size], dtype=np.float32)
            return array

        if self.file_inferences:
            first_key = next(iter(self.file_inferences))
            extension = self.file_inferences[first_key].extension
            if extension == '.npz':
                if field_name not in self.data.files:
                    print(f"File does not contain '{field_name}'")
                    return None
            elif extension == '.npy':
                if field_name not in self.data:
                    print(f"File does not contain '{field_name}")
                    return None
            else:
                raise RuntimeError(f"Unsupported filename extension '{self.extension}'")

        array = self.data.get(field_name)
        if array is None:
            print(f"ERROR: Could not get field '{field_name}'")
            return None

        if not isinstance(array, np.ndarray):
            print(f"ERROR: Unsupported field '{field_name}' is not an array")
            return None

        if self.unnormalize_data and (field_name == 'coordinates' or field_name == 'surface_coordinates'):
            print(f"WARNING: Unnormalizing '{field_name}' data! (array.shape={array.shape}, dtype={array.dtype})")

            array = HALF_SIZE * array + POSITION
            array = array.astype(np.float32)

        return array

    def _data_preloader(self):
        '''Cache data from file to a memory'''

        if not self.preload_data:
            return

        print("Caching data to a memory...")

        for file_inference in self.file_inferences.values():
            file_inference.load_data()
            self.data = file_inference.get_data()
            file_arrays = {}
            for field_name in self.field_names:
                array = self._get_array(field_name)
                if array is not None:
                    file_arrays[field_name] = array
                else:
                    print(f"WARNING: Could not prelaoad a field '{field_name}' not in a file")

            if self.prune_points:
                fields_to_prune = ['velocity', 'coordinates', 'pressure']
                for field_name in fields_to_prune:
                    file_arrays[field_name] = Service.prune_point_count(file_arrays[field_name], field_name)

            file_inference.arrays = file_arrays

        self.data = None

    def _request_data(self, config_request):
        '''Get data for current config request'''

        if self.file_inferences:
            file_index = self._get_data_from_file(config_request)
        else:
            file_index = -1
            self._get_data_from_script(config_request)

        if not self.data:
            print(f"WARNING: Could not load data for id {config_request['id']}")

        return file_index

    def _get_data_to_send(self, file_index, field_name, config_request):

        if self.file_inferences and self.preload_data and file_index >= 0:
            if field_name in self.file_inferences[file_index].arrays:
                array = self.file_inferences[file_index].arrays[field_name]
        else:
            array = self._get_array(field_name)
            if array is None:
                return None, None

        # Send the metadata
        metadata = {
            'timestamp': config_request['timestamp'],
            'field_name': str(field_name),
            'id': int(config_request['id']),
            'shape': array.shape,
            'dtype': str(array.dtype),
        }
        return metadata, array

    def load_uploaded_files(self, stl_filename, streamlines_filename):
        """
        Load STL file and streamlines JSON from uploaded files directory

        Args:
            stl_filename: Name of the STL file
            streamlines_filename: Name of the streamlines JSON file

        Returns:
            Dictionary with coordinates, velocity, streamlines_data, and bounding_box_dims
        """
        output_data = {}

        try:
            # Build paths
            stl_dir = Path(self.uploaded_files_dir) / "stl"
            streamlines_dir = Path(self.uploaded_files_dir) / "streamlines"

            stl_path = stl_dir / stl_filename
            streamlines_path = streamlines_dir / streamlines_filename

            print(f"Looking for STL at: {stl_path}")
            print(f"Looking for streamlines at: {streamlines_path}")

            # Load STL file
            if stl_path.exists():
                print(f"Loading STL file: {stl_path}")
                stl_mesh = trimesh.load(str(stl_path))

                # Get bounding box
                bounds = stl_mesh.bounds  # [[xmin, ymin, zmin], [xmax, ymax, zmax]]
                output_data["bounding_box_dims"] = bounds.astype(np.float32)

                # Store STL mesh data
                output_data["stl_vertices"] = stl_mesh.vertices.astype(np.float32)
                output_data["stl_faces"] = stl_mesh.faces.astype(np.int32)

                self.current_stl_path = str(stl_path)
                print(f"Loaded STL: {stl_mesh.vertices.shape[0]} vertices, bounds: {bounds}")
            else:
                print(f"WARNING: STL file not found: {stl_path}")
                # Use default bounds
                output_data["bounding_box_dims"] = BOUNDS.astype(np.float32)

            # Load streamlines JSON
            if streamlines_path.exists():
                print(f"Loading streamlines JSON: {streamlines_path}")
                with open(streamlines_path, 'r') as f:
                    streamlines_data = json.load(f)

                # Store the full streamlines data for direct use by Kit App
                output_data["streamlines_json"] = streamlines_data

                # Also convert to coordinates/velocity format for compatibility
                all_points = []
                all_velocities = []

                for streamline in streamlines_data.get("streamlines", []):
                    path = np.array(streamline["path"], dtype=np.float32)

                    # Use scalar values as velocity magnitudes if available
                    if "scalar" in streamline:
                        scalars = np.array(streamline["scalar"], dtype=np.float32)
                        # Create velocity vectors (assuming flow in X direction for now)
                        # This is a simplified representation
                        velocities = np.column_stack([scalars, np.zeros_like(scalars), np.zeros_like(scalars)])
                    else:
                        # Default velocity
                        velocities = np.ones((len(path), 3), dtype=np.float32) * 30.0

                    all_points.append(path)
                    all_velocities.append(velocities)

                if all_points:
                    output_data["coordinates"] = np.vstack(all_points)
                    output_data["velocity"] = np.vstack(all_velocities)
                    output_data["pressure"] = np.zeros((len(output_data["coordinates"]),), dtype=np.float32)

                    print(f"Loaded {len(streamlines_data.get('streamlines', []))} streamlines")
                    print(f"Total points: {len(output_data['coordinates'])}")

                self.current_streamlines_path = str(streamlines_path)
            else:
                print(f"WARNING: Streamlines file not found: {streamlines_path}")
                # Create minimal dummy data
                output_data["coordinates"] = np.zeros((100, 3), dtype=np.float32)
                output_data["velocity"] = np.ones((100, 3), dtype=np.float32) * 30.0
                output_data["pressure"] = np.zeros((100,), dtype=np.float32)

            return output_data

        except Exception as e:
            print(f"ERROR loading uploaded files: {e}")
            import traceback
            traceback.print_exc()
            return None