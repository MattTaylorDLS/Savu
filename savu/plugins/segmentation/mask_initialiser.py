# Copyright 2019 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. module:: Plugin to initialise a binary mask for level sets and distance transform segmentations
   :platform: Unix
   :synopsis: Plugin to initialise a binary mask for level sets and distance transform segmentations

.. moduleauthor:: Daniil Kazantsev <scientificsoftware@diamond.ac.uk>
"""

from savu.plugins.plugin import Plugin
from savu.plugins.driver.cpu_plugin import CpuPlugin
from savu.plugins.utils import register_plugin

import numpy as np

# using Morphological snakes module from
# https://github.com/pmneila/morphsnakes
from morphsnakes import circle_level_set

@register_plugin
class MaskInitialiser(Plugin, CpuPlugin):
    """
    Plugin to initialise a binary mask for level sets and distance transform segmentations.\
    Seeds are currently given by providing coordinates of two points X0,Y0,Z0 and X1,Y1,Z1 (of a certain radius)\
    from which a connecting line will be drawn between them (a 3D pipe through space). 
    Note that Z coordinate is provided in a sense of VOLUME_XY - vertical pattern

    :param init_coordinates: X0,Y0,Z0 and X1,Y1,Z1 coordinates of two points. Default: [10, 10, 0, 20, 20, 20].
    :param circle_radius: The seed will be initialised with a circle of radius. Default: 5.
    :param out_datasets: The default names . Default: ['INIT_MASK'].
    """

    def __init__(self):
        super(MaskInitialiser, self).__init__("MaskInitialiser")

    def setup(self):
        in_dataset, out_dataset = self.get_datasets()
        in_pData, out_pData = self.get_plugin_datasets()
        in_pData[0].plugin_data_setup('VOLUME_YZ', 'single')
        
        out_dataset[0].create_dataset(in_dataset[0], dtype=np.uint8)
        out_pData[0].plugin_data_setup('VOLUME_YZ', 'single')
        self.full_input_shape = in_dataset[0].get_shape()
        
    def pre_process(self):
        # extract given parameters
        self.init_coordinates = self.parameters['init_coordinates']
        self.circle_radius = self.parameters['circle_radius']
        
        self.coordX0 = self.init_coordinates[0]
        self.coordY0 = self.init_coordinates[1]
        self.coordZ0 = self.init_coordinates[2]
        self.coordX1 = self.init_coordinates[3]
        self.coordY1 = self.init_coordinates[4]
        self.coordZ1 = self.init_coordinates[5]
        
        steps = self.coordZ1 - self.coordZ0
        self.distance = np.sqrt((self.coordX1 - self.coordX0)**2 + (self.coordY1 - self.coordY0)**2)
        self.d_dist = self.distance/(steps - 1.0)
        self.d_step = self.d_dist

    def process_frames(self, data):
        # get the index of a current frame
        index_current = self.get_plugin_in_datasets()[0].get_current_frame_idx()
        if ((index_current >= self.coordZ0) & (index_current <= self.coordZ1)):
            self.d_step = (index_current - self.coordZ0)*self.d_dist
            t = self.d_step/self.distance
            x_t = np.round((1.0 - t)*self.coordX0 + t*self.coordX1)
            y_t = np.round((1.0 - t)*self.coordY0 + t*self.coordY1)
            if (self.coordX0 == self.coordX1):
                x_t = self.coordX0
            if(self.coordY0 == self.coordY1):
                y_t = self.coordY0
            mask = np.uint8(circle_level_set(np.shape(data[0]), (np.round(y_t[0]), np.round(x_t[0])), self.circle_radius))
        else:
            mask = np.uint8(np.zeros(np.shape(data[0])))
        return [mask]

    def nInput_datasets(self):
        return 1
    def nOutput_datasets(self):
        return 1
    def get_max_frames(self):
        return 'single'