import nibabel as nb
import numpy as np
import os
import sys

#import argparse
#parser = argparse.ArgumentParser(description = 'Remove streamlines intersecting the ROI. Writes the masked streamlines (_masked) and those that were cut out (_cut).\n Output <fname>_masked.trk and <fname>_cut.trk files to the input directory')
#parser.add_argument('-i', '--input', nargs='+', type=str, required=True, help='streamlines file, trk format')
#parser.add_argument('-m', '--mask', type=str,  required=True, help='ROI mask file (same affine, binary, 3d)')
#
#track_file=parser.parse_args().input
#mask_file=parser.parse_args().mask

"""
March 15, 2014
Christopher J. Steele

Program to mask streamlines data in trackvis format (trk) with provided ROI
 - this will potentially be useful for masking connectivity depending on provided lesion locations
 - this file could change to include the necessary measures/calculations required create the connectivity matrices that can be used here 

Outputs the streamlines without those that cross the ROI (_masked.trk) and the streamlines that were removed (_cut.trk)
These files are placed in the input directory (unless this is still hard-coded for testing!)
Voxel settings and affine *should* be correct if all files were generated from the same base files

XXX not sure if this will be a stand-alone or for use as an import function
"""
def mask_streamlines(track_fname,mask_fname):
    '''
    Christopher J. Steele
    March 15, 2014
    
    Evaluates the crossing between streamlines in trackvis format (track_fname [trk]) and mask roi (mask_fname).
    Returns masked_streamlines, original header, and the streamlines that were cut 
       
    '''

    streamlines,hdr=nb.trackvis.read(track_fname,False) #read the track file into header and data, assume voxels locations are in native trackvis format
    mask_file=nb.load(mask_fname)
    mask_data=mask_file.get_data()

    maskVoxelSize = mask_file.get_header().get_zooms()    
    streamlines_aff=nb.trackvis.aff_from_hdr(hdr,True)
    mask_aff=mask_file.get_affine()

    #check if we are using an ROI file with the same dimensions and affine as our streamlines
    if not(np.array_equal(streamlines_aff,mask_aff)):
        print('The affine matrices of your tracks and rois files are not the same.\nExiting.')
        sys.exit()
    else:
        print('Affine matrices match, proceeding to mask your streamlines with the provided ROI')
    
    num_fibs=len(streamlines)
    print('Number of original streamlines: {num}'.format(num=num_fibs))
    
    #loop through each stream and determine if it crosses the roi(s)
    masked_streamlines=[] #left over streamlines after cutting from ROI
    cut_streamlines=[] #the streamlines that were cut
    i=0
    print('Processing streamlines (updated every 50 streams): ')
    for stream in streamlines: #across all streamlines
        i+=1
        if np.mod(i,50)==0:
            p=i/num_fibs*100
            print np.ceil(p),
            sys.stdout.flush()
        if not(rois_crossed(stream,mask_data,maskVoxelSize)):
            masked_streamlines.append(stream)     
        else:
            cut_streamlines.append(stream)
    print('\n') #carriage return to finish after the updating of the progress
    return masked_streamlines, hdr, cut_streamlines

def rois_crossed(stream,roiData,voxelSize,verbose=False):
    '''
    Christopher J. Steele
    March 14, 2014
    adapted from nipype.interfaces.cmtk 

    checks to see if any voxel locations in stream pass through the roi
    if so, return True, otherwise False
    '''
    
    stream=stream[0] # convert it to a list with 3 columns (x,y,z)
    n_points = len(stream)#[0])
    for j in xrange(0, n_points):
        # store point, convert from mm to voxel location
        x = int(stream[j, 0] / float(voxelSize[0]))
        y = int(stream[j, 1] / float(voxelSize[1]))
        z = int(stream[j, 2] / float(voxelSize[2]))
        
        if roiData[x, y, z] == 1:
            if verbose == True:
                print('Voxel crossed at: ' + str(x)+','+str(y)+','+str(z))
            return True
        else:
            pass
    return False #no crossings of stream and ROI

#%%


io_dir='/home/chris/scripts/python/ni_utils'
track_file=os.path.join(io_dir,'XXX_TEST_data_CSD_tracked_L_VI_5K.trk')
lesion_mask_file=os.path.join(io_dir,'XXX_TEST_lesion_mask.nii.gz')

out_masked_fname = os.path.join(os.path.split(track_file)[0],str.split(os.path.split(track_file)[1],".")[0]) + '_XxX_' + str.split(os.path.split(lesion_mask_file)[1],".")[0] + '_masked.trk'
out_cut_fname = os.path.join(os.path.split(track_file)[0],str.split(os.path.split(track_file)[1],".")[0]) + '_XxX_' + str.split(os.path.split(lesion_mask_file)[1],".")[0] + '_cut.trk'

masked_streamlines, streamlines_hdr, cut_streamlines=mask_streamlines(track_file,lesion_mask_file)

print('Number of streamlines after masking {num}'.format(num=len(masked_streamlines)))
print(out_masked_fname+'\n')
hdr_new=streamlines_hdr.copy()
hdr_new['n_count']=len(masked_streamlines)
nb.trackvis.write(out_masked_fname,masked_streamlines,hdr_new)
hdr_new['n_count']=len(cut_streamlines)
print('Number of streamlines that were cut {num}'.format(num=len(cut_streamlines)))
print(out_cut_fname+'\n')
nb.trackvis.write(out_cut_fname,cut_streamlines,hdr_new)
