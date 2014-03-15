import nibabel as nb
import numpy as np
#import nipype.interfaces.cmtk as cmtk #connectivity mapping toolkit
import os
import sys

#import argparse
#parser = argparse.ArgumentParser(description = 'Remove streamlines intersecting the ROI. Writes the masked streamlines (_masked) and those that were cut out (_cut).\n Output <fname>_masked.trk and <fname>_cut.trk files to the input directory')
#parser.add_argument('-i', '--input', nargs='+', type=str, required=True, help='streamlines file, trk format')
#parser.add_argument('-m', '--mask', type=str,  required=True, help='ROI mask file (same affine, binary, 3d)')
#
#track_file=parser.parse_args().input
#mask_file=parser.parse_args().mask


io_dir='/home/chris/scripts/python/ni_utils'
track_file=os.path.join(io_dir,'XXX_TEST_data_CSD_tracked_L_VI_5K.trk')
out_file=os.path.join(io_dir,'XXX_TEST_data_CSD_tracked_L_VI_5K_ROIMASKED.trk')
out_cut_file=os.path.join(io_dir,'XXX_TEST_data_CSD_tracked_L_VI_5k_ROIMASKED_cut.trk')
lesion_mask_file=os.path.join(io_dir,'XXX_TEST_lesion_mask.nii.gz')
streamlines,hdr=nb.trackvis.read(track_file,False) #read in the track file into header and data, assume voxels locations are in native trackvis format

mask_file=_file=nb.load(lesion_mask_file)
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
    
#nb.trackvis.write(os.path.join(io_dir,'XXX_XXX_inout.trk'),streamlines,hdr) #test reading in and writing out without flipping x

#%% 
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
    #print(n_points)
    #print('Streamline np.np.shape: {num}'.format(num=np.shape(stream)))
    for j in xrange(0, n_points):
        #altered=False #we have not played around with the xyz values to make sure that they fit inside our bounding box (XXX 0 vs 1-based problem??)
        #print(j)
        # store point, convert from mm to voxel location
        x = int(stream[j, 0] / float(voxelSize[0]))
        y = int(stream[j, 1] / float(voxelSize[1]))
        z = int(stream[j, 2] / float(voxelSize[2]))

        #check to see if we are outside of dimensions that are in the roiData. If so, something has gone wrong with voxel dimensions and the user should NOT use this data        
        #if x>=np.shape(roiData)[0]:
            #x=np.shape(roiData)[0]-1
            #altered=True
        #if y>=np.shape(roiData)[1]:
            #y=np.shape(roiData)[1]-1
            #altered=True
        #if z>=np.shape(roiData)[2]:
            #z=np.shape(roiData)[2]-1
            #altered=True
        #if altered:
            #pass
            #print('At least one coordinate was altered')
        #print('Voxel: ' + str(x)+','+str(y)+','+str(z))
        if roiData[x, y, z] == 1:
            if verbose == True:
                print('Voxel crossed at: ' + str(x)+','+str(y)+','+str(z))
            return True
        else:
            pass
    #print('No crossings of stream and roi')
    return False

#%% 
num_fibs=len(streamlines)
print('Number of original streamlines: {num}'.format(num=num_fibs))

masked_streamlines=[] #left over streamlines after cutting from ROI
cut_streamlines=[] #the streamlines that were cut
i=0

#loop through each stream and determine if it crosses the roi(s)
print('Processing streamlines (updated every 50 streams): ')
for stream in streamlines: #across all streamlines
    i+=1
    if np.mod(i,50)==0:
        #print('.'),
        p=i/num_fibs*100
        print np.ceil(p),
        #sys.stdout.write("\r%i%%" %p)    # or print >> sys.stdout, "\r%d%%" %i,
        #sys.stdout.flush()
        #print >> sys.stdout, "\r%d%%" %p,
        sys.stdout.flush()
    if not(rois_crossed(stream,mask_data,maskVoxelSize)):
        masked_streamlines.append(stream)     
    else:
        cut_streamlines.append(stream)
        #print('Bad boy, you are in my ROI!')
print('\n') #carriage return to finish after the updating of the progress
    
print('Number of streamlines after masking {num}'.format(num=len(masked_streamlines)))
hdr_new=hdr.copy()
hdr_new['n_count']=len(masked_streamlines)
nb.trackvis.write(out_file,masked_streamlines,hdr_new)
hdr_new['n_count']=len(cut_streamlines)
print('Number of streamlines that were cut {num}'.format(num=len(cut_streamlines)))
nb.trackvis.write(out_cut_file,cut_streamlines,hdr_new)
nb.trackvis.write(os.path.join(io_dir,'XXX_XXX_inout.trk'),streamlines,hdr)
