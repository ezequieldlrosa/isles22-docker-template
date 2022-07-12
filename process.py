import SimpleITK
import numpy as np
import json
import os
from evalutils import SegmentationAlgorithm
from pathlib import Path

DEFAULT_INPUT_PATH = Path("/input/")
DEFAULT_ALGORITHM_OUTPUT_IMAGES_PATH = Path("/output/images/")

class Threshold_model():
    def __init__(self):
        self.debug = False  #False for running the docker!

        if self.debug:
            self._input_path = Path('/Users/edelarosa/Documents/Repos/algorithm_docker/threshold_model/test')
            self._output_path = Path('/Users/edelarosa/Documents/Repos/algorithm_docker/threshold_model/test/output')
            self._algorithm_output_path = self._output_path / 'images'/ 'stroke-lesion-segmentation'
            self._output_file = self._output_path / 'results.json'
            self._case_results = []

        else:
            self._input_path = DEFAULT_INPUT_PATH
            self._output_path = DEFAULT_ALGORITHM_OUTPUT_IMAGES_PATH
            self._algorithm_output_path = self._output_path / 'stroke-lesion-segmentation'
            self._output_file = self._output_path / 'results.json'
            self._case_results = []

    def predict(self):
        """
        Input   input_data, dict.
                The dictionary contains 3 images and 3 json files.
                keys:  'dwi_image' , 'adc_image', 'flair_image', 'dwi_json', 'adc_json', 'flair_json'

        Output  prediction, array.
                Binary mask encoding the lesion segmentation (0 background, 1 foreground).
        """

        # Get all image inputs.
        dwi_image = SimpleITK.GetArrayFromImage(self.input_data['dwi_image'])
        adc_image = SimpleITK.GetArrayFromImage(self.input_data['adc_image'])
        flair_image = SimpleITK.GetArrayFromImage(self.input_data['flair_image'])

        # Get all json inputs.
        dwi_json, adc_json, flair_json = self.input_data['dwi_json'], self.input_data['adc_json'], self.input_data['flair_json']

        ### Beginning of your prediction method.
        #todo Please replace with your best model here!
        #As an example, we'll segment the DWI using a 99th-percentile intensity cutoff.

        dwi_cutoff = np.percentile(dwi_image[dwi_image > 0], 99)
        prediction = dwi_image > dwi_cutoff

        ### End of your prediction method.

        return prediction.astype(int)

    def process_isles_case(self):

        # Get origin, spacing and direction from the DWI image.
        origin, spacing, direction = self.input_data['dwi_image'].GetOrigin(),\
                                     self.input_data['dwi_image'].GetSpacing(),\
                                     self.input_data['dwi_image'].GetDirection()

        # Segment images.
        prediction = self.predict() #todo: this is the function you need to update!

        # Build the itk object.
        output_image = SimpleITK.GetImageFromArray(prediction)
        output_image.SetOrigin(origin), output_image.SetSpacing(spacing), output_image.SetDirection(direction)

        # Write resulting segmentation to output location.

        if not self._algorithm_output_path.exists():
            os.makedirs(str(self._algorithm_output_path))
        output_image_path = self._algorithm_output_path / self._input_filename
        SimpleITK.WriteImage(output_image, str(output_image_path))

        # Write segmentation file path to result.json.

        if output_image_path.exists():
            self.json_result = {"outputs": [dict(type="hola", filename=output_image_path.name)]}
            self._case_results.append(self.json_result)
            self.save()

        else:
            print('Prediction failed')

    def load_isles_case(self):
        """ Loads the 6 inputs of ISLES22 (3 MR images, 3 metadata json files accompanying each MR modality).
        Note: Cases missing the metadata will still have a json file, though their fields will be empty. """

        # Get MR data paths.
        dwi_image_path = self.get_file_path(slug='dwi-brain-mri', filetype='image', input=True)
        adc_image_path = self.get_file_path(slug='adc-brain-mri', filetype='image', input=True)
        flair_image_path = self.get_file_path(slug='flair-brain-mri', filetype='image', input=True)

        # Get MR metadata paths.
        dwi_json_path = self.get_file_path(slug='dwi-mri-acquisition-parameters', filetype='json', input=True)
        adc_json_path = self.get_file_path(slug='adc-mri-parameters', filetype='json')
        flair_json_path = self.get_file_path(slug='flair-mri-acquisition-parameters', filetype='json', input=True)

        input_data = {'dwi_image': SimpleITK.ReadImage(str(dwi_image_path)), 'dwi_json': json.load(open(dwi_json_path)),
                      'adc_image': SimpleITK.ReadImage(str(adc_image_path)), 'adc_json': json.load(open(adc_json_path)),
                      'flair_image': SimpleITK.ReadImage(str(flair_image_path)), 'flair_json': json.load(open(flair_json_path))}

        # Get the DWI filename to later rename the output.
        self._input_filename = str(dwi_image_path).split('/')[-1]
        self.input_data = input_data

    def get_file_path(self, slug, filetype='image', input=True):
        """ Gets the path for each MR image/json file."""
        if input:
            imagesdir = self._input_path
        else:
            imagesdir = self._output_path

        if filetype == 'image':
            file_list = [f for f in (imagesdir / 'images' / slug).glob('*.mha')]
        elif filetype == 'json':
            file_list = [f for f in (imagesdir / slug).glob('*.json')]

        # check that there is a single file
        if len(file_list) != 1:
            print('Loading error')
        else:
            return file_list[0]

    def save(self):
        with open(str(self._output_file), "w") as f:
            json.dump(self._case_results, f)

    def process(self):
        self.input_case = self.load_isles_case()
        self.process_isles_case()

if __name__ == "__main__":
    Threshold_model().process()
