#!/usr/bin/env python3
###############################################################################
#                                                                             #
#    This program is free software: you can redistribute it and/or modify     #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This program is distributed in the hope that it will be useful,          #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this program. If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

__author__      = "Joel Boyd"
__copyright__   = "Copyright 2017"
__credits__     = ["Joel Boyd"]
__license__     = "GPL3"
__version__     = "0.0.7"
__maintainer__  = "Joel Boyd"
__email__       = "joel.boyd near uq.net.au"
__status__      = "Development"
 
###############################################################################
# Imports
import logging
# Local
from enrichm.databases import Databases
###############################################################################

class KeggMatrix:
    
    def __init__(self, matrix, transcriptome):
        d = Databases()
        self.r2k = d.r2k
        logging.info("Parsing input matrix: %s" % matrix)
        self.orthology_matrix \
                 = self._parse_matrix(matrix)
        logging.info("Calculating reaction abundances")
        self.reaction_matrix  \
                 = self._calculate_abundances(self.r2k, self.orthology_matrix)
        
        if transcriptome:
            logging.info("Parsing input transcriptome: %s" % transcriptome)
            self.orthology_matrix_transcriptome \
                        = self._parse_matrix(transcriptome)
            
            logging.info("Calculating reaction transcriptome abundances")
            self.reaction_matrix_transcriptome \
                 = self._calculate_abundances(self.r2k, 
                                              self.orthology_matrix_transcriptome)
            
            logging.info("Calculating normalized expression abundances")
            self.orthology_matrix_expression \
                = self._calculate_expression_matrix(self.orthology_matrix, 
                                        self.orthology_matrix_transcriptome)
            
            logging.info("Calculating reaction expression abundances")
            self.reaction_matrix_expression  \
                 = self._calculate_abundances(self.r2k, 
                                              self.orthology_matrix_expression)
   
    def _calculate_expression_matrix(self, matrix, transcriptome_matrix):
        '''
        '''
        output_dictionary = {}
        for sample, abundances in transcriptome_matrix.items():
            output_dictionary[sample] = {}
            for ko, abundance in abundances.items():

                if ko in matrix[sample]:
                    mg_abundance = float(matrix[sample][ko])
                    mt_abundance = float(abundance)
                    if mg_abundance>0:
                        output_dictionary[sample][ko] \
                                = float(abundance)/float(matrix[sample][ko])
                else:
                    continue 
                    # for now ignore genes that are expressed, but not detected
                    # in the metagenome.
        return output_dictionary        
        
    def _parse_matrix(self, matrix):
        
        output_dict = {}
        
        for idx, line in enumerate(open(matrix)):
            sline = line.strip().split('\t')
            if idx==0:
                self.sample_names = sline[1:]
                    
                for sample in self.sample_names: 
                    output_dict[sample] = {}
            else:   
                ko_id      = sline[0]
                abundances = sline[1:]
                
                for abundance, sample in zip(abundances, self.sample_names):
                    output_dict[sample][ko_id] = float(abundance)
        return output_dict
    
    def group_abundances(self, samples, reference_dict):
        
        output_dict = {}        
        for sample in samples:
            new_dict = {key:entry for key,entry in reference_dict.items() if 
                        key in samples}

            reference_list = new_dict[new_dict.keys()[0]].keys()
            for reference in reference_list:
                # If samples are missing from stored data, this will crash 
                try:
                    abundances = [new_dict[sample][reference] for sample in samples]
                    average    = sum(abundances)/float(len(abundances))
                    if average > 0:
                        output_dict[reference] = average
                except:
                    raise Exception("metadata description does not match \
input matrix")
        return output_dict
                          
    def _calculate_abundances(self, reference_dict, matrix_dict):
        output_dict_mean   = {}
        for sample, ko_abundances in matrix_dict.items():
            output_dict_mean[sample]   = {}
            for reaction, ko_list in reference_dict.items():


                abundances = []
                for ko in ko_list:
                    if ko in matrix_dict[sample]:
                        abundances.append(matrix_dict[sample][ko])
                    else:
                        logging.debug("ID not found in input matrix: %s" % ko)
                if any(abundances):
                    abundance_mean = sum(abundances)/len(abundances)
                else:
                    abundance_mean = 0
                output_dict_mean[sample][reaction] = abundance_mean
        return output_dict_mean
