#!/usr/bin/env python

"""
Christopher J. Steele
March 2014

Hard segmentation of volume based on tract-specific volumes containing the number of streamlines
that pass through each voxel

"""

import os
import argparse
import numpy as np
import nibabel as nb

parser = argparse.ArgumentParser(description = 'Calculate tract-based segmentation of input voxel-wise streamline counts.\n Output <fname>_seg_idx.nii.gz (index-based segmentation (1...n)) and <fname>_seg_pct.nii.gz (index + proportion) files to the input directory')
parser.add_argument('-i', '--input', nargs='+', type=str, required=True, help='3D voxel-wise streamline count files (2 or more)')
parser.add_argument('-o', '--out', type=str,  required=True, help='Output file name')

files=parser.parse_args().input
print(files)
out_basename=parser.parse_args().out
#mask_name=parser.parse_args().mask
#mask_img=nb.load(mask_name)
#mask_data=mask_img.get_data()

if os.path.dirname(out_basename) == '': #if they didn't bother to set a path, same as input
    out_dir=os.path.dirname(files[0])
else:
    out_dir=os.path.dirname(out_basename)

seg_idx_fname = os.path.join(out_dir,out_basename) + '_seg_idx.nii.gz'
seg_tot_fname = os.path.join(out_dir,out_basename) + '_seg_tot.nii.gz'
seg_prt_fname = os.path.join(out_dir,out_basename) + '_seg_prt.nii.gz'
seg_pct_fname = os.path.join(out_dir,out_basename) + '_seg_pct.nii.gz'

#working_dir="/scr/alaska2/steele/Projects/Working/7T/CBTractography/processing/dmri_mrtrix_dti/dwiproc/tractography/_id_BK1T/probCSDstreamtrack"
#files = get_ipython().getoutput(u'ls *TDI_0*')
#files = ['HIV_TDI_0p2.nii.gz','HV_TDI_0p2.nii.gz','HVI_TDI_0p2.nii.gz','crusI_TDI_0p2.nii.gz','crusII_TDI_0p2.nii.gz']
#files = ['HIV_TDI_0p05.nii.gz','HV_TDI_0p05.nii.gz','HVI_TDI_0p05.nii.gz','crusI_TDI_0p05.nii.gz','crusII_TDI_0p05.nii.gz']



#np.concatenate((np.zeros((2,2))[...,np.newaxis], np.ones((2,2))[...,np.newaxis]), axis=2)
#%% load the data and create a 4D file
#files=['XXX_TEST_lesion_mask.nii.gz','XXX_TEST_lesion_mask_2.img']

data_list = [nb.load(fn).get_data()[...,np.newaxis] for fn in files] #load all of the files
combined = np.concatenate(data_list, axis=-1) #concatenate all of the input data
print('You have input {num} files for segmentation'.format(num=combined.shape[3]))

combined = np.concatenate((np.zeros_like(data_list[0]),combined),axis=-1) #add a volume of zeros to padd axis and make calculations work correctly

#%% hard segmentation (tract w/ largest number of streamlines in each voxel wins)
# uses argmax to return the index of the volume that has the largest value (adds 1 to be 1-based)
hard_seg=combined.argmax(axis=-1) #now we have a 1-based segmentation (largest number in each voxel)
hard_seg[combined.std(axis=-1) == 0] = 0 #where there is no difference between volumes, this should be the mask, set to 0


#%% create soft segmentation to show strength of the dominant tract in each voxel
seg_part = np.zeros_like(hard_seg)
seg_temp = np.zeros_like(hard_seg)
seg_total = combined.sum(axis=-1)

idx=1
for seg in files:
    seg_temp = combined[:,:,:,idx] #get value at this voxel for this tract seg (-1 for 0-based index of volumes)
    seg_part[hard_seg==idx] = seg_temp[hard_seg==idx] #1-based index of segmentation
    idx +=1


#seg_pct = seg_part/seg_total
seg_pct = np.where(seg_total > 0, seg_part.astype(np.float64)/seg_total.astype(np.float64),0) #where there is no std (regions with no tracts) return 0, otherwise do the division
#seg_pct[seg_pct==float('-Inf')] = 999

#convert so that each segmentation goes from above its segmented to number to just below +1
#.001 added to make sure that segmentations where tracts are 100% do not push into the next segmentation (not necessary depending on how the images are displayed)
#1st is 1-1.999, 2nd is 2-3.... (though the values should always be above the integer b/c of the segmentation
seg_pct=np.add(seg_pct,hard_seg) #add them and subtract a value, now the values are percentages of the segmentations for each number
#seg_pct=np.where(seg_pct>0,np.subtract(seg_pct,.001),0)

#%%save
nii = nb.load(files[0])
new_nii = nb.Nifti1Image(hard_seg, nii.get_affine(), nii.get_header())
new_nii.to_filename(seg_idx_fname)

new_nii = nb.Nifti1Image(seg_total, nii.get_affine(), nii.get_header())
new_nii.to_filename(seg_tot_fname)

new_nii = nb.Nifti1Image(seg_part, nii.get_affine(), nii.get_header())
new_nii.to_filename(seg_prt_fname)

new_nii = nb.Nifti1Image(seg_pct, nii.get_affine(), nii.get_header())
new_nii.to_filename(seg_pct_fname)
