#!/usr/bin/env python

'''
Feb 23, 2014
Chris Steele

Small program that reads in one or more fmri timecourses and mask (single or multiple ROIs) and outputs a 4d file 
with the mean signal in ROIs over time, along with a file with the standard deviations. 
All voxels in the ROI are given the same value. This is useful for pre-processing low SNR fMRI analyses
that have specific ROIs.
Output files are placed in the same location as the inputs

usage: create_roi_volumes.py -i <file1> ... <fileN>  -m <ROI_mask>
'''

import os
import numpy as np
import nibabel as nb
#import multiprocessing as mp
import argparse

parser = argparse.ArgumentParser(description = 'Calculate mean and standard deviation for ROIs, fill ROIs with these values.\n Output <fname>_ROI_avg.nii.gz and <fname>_ROI_std.nii.gz files to the input directory')
parser.add_argument('-i', '--input', nargs='+', type=str, required=True, help='fmri timecourse file(s) (one or more, 4d)')
parser.add_argument('-m', '--mask', type=str,  required=True, help='ROI mask file (unique integers, 3d)')

fmri_names=parser.parse_args().input
mask_name=parser.parse_args().mask
mask_img=nb.load(mask_name)
mask_data=mask_img.get_data()

#get a list of the rois within the mask
rois=np.unique(mask_data[mask_data != 0])
print('Found ' + str(len(rois)) + ' ROIs in the provided mask file.')

for fmri_name in fmri_names:
	fmri_img=nb.load(fmri_name)
	fmri_data=fmri_img.get_data()

	if not fmri_data[...,0].shape == mask_data.shape:
		print('Your mask file does not have the same dimensions as your data (x,y,z). fmri: ' + str(np.shape(fmri_data)) + ', mask: ' + str(np.shape(mask_data)))
	else:
		print('Mask and fmri dimensions fit. Good job.')


	out_avg = np.zeros_like(fmri_data) #create array of same shape and type as the input data, this will become the output volume
	out_std = np.zeros_like(fmri_data)
	avg_fname = os.path.join(os.path.split(fmri_name)[0],str.split(os.path.split(fmri_name)[1],".")[0]) + '_ROI_avg.nii.gz'
	std_fname = os.path.join(os.path.split(fmri_name)[0],str.split(os.path.split(fmri_name)[1],".")[0]) + '_ROI_std.nii.gz'

	for roi in rois:
		print('Processing ROI ' + str(roi) + ' ...'),
		ts = fmri_data[mask_data == roi] #creates a 2d array of vox X time for ROI (where each vox is from masked locations)	
		ts_avg = np.average(ts,axis=0) #average across voxels, not time
		out_avg[mask_data == roi] = ts_avg #assign the avg value to each voxel in the volume, for each volume (XXX i think!)
		#out_avg[mask_data==roi]=np.average(fmri_data[mask_data==roi],axis=0) #in a single line!
		out_std[mask_data == roi] = np.std(ts,axis=0) #standard deviation
		print(' success.')

	print('Saving average and standard deviation of the provided ROIs.\n' + avg_fname + '\n' + std_fname)
	nb.Nifti1Image(out_avg,fmri_img.get_affine()).to_filename(avg_fname)
	nb.Nifti1Image(out_std,fmri_img.get_affine()).to_filename(std_fname)

