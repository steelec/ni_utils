import nibabel as nb
import numpy as np
import nipype.interfaces.cmtk as cmtk #connectivity mapping toolkit
    
track_file='/scr/alaska2/steele/Projects/Working/7T/CBTractography/processing/dmri_mrtrix_dti/dwiproc/tractography/_id_BK1T/deterCSDstreantrack/XXX_TEST_data_CSD_tracked_L_VI_5K.trk'
out_file='/scr/alaska2/steele/Projects/Working/7T/CBTractography/processing/dmri_mrtrix_dti/dwiproc/tractography/_id_BK1T/deterCSDstreantrack/XXX_TEST_data_CSD_tracked_L_VI_5K_ROIMASKED.trk'

lesion_mask_file='/scr/alaska2/steele/Projects/Working/7T/CBTractography/processing/dmri_mrtrix_dti/dwiproc/tractography/_id_BK1T/deterCSDstreantrack/XXX_TEST_lesion_mask.nii.gz'
streamlines,hdr=nb.trackvis.read(track_file,False,points_space='rasmm') #read in the track file into header and data

mask=_file=nb.load(lesion_mask_file)
mask_data=mask_file.get_data()
maskVoxelSize = mask.get_header().get_zooms()

#%% 
num_fibs=len(streamlines)
print('Number of original streamlines: {num}'.format(num=num_fibs))

masked_streamlines=[]
i=0
for stream in streamlines: #across all streamlines
    print(i),
    i+=1
    if not(rois_crossed(stream,mask_data,maskVoxelSize)):
        masked_streamlines.append(stream)     
    else:
        print('Bad boy, you are in my ROI!')

print('Number of streamlines after masking {num}'.format(num=len(masked_streamlines)))
hdr_new=hdr.copy()
hdr_new['n_count']=len(masked_streamlines)
nb.trackvis.write(out_file,masked_streamlines,hdr_new)

#%% 
def rois_crossed(stream,roiData,voxelSize):
    '''
    from nipype.interfaces.cmtk 
    checks to see if any voxel locations in stream (in mm voxel) pass through the roi
    if so, return True, otherwise False
    '''
    stream=stream[0] # convert it to a list with 3 columns (x,y,z)
    n_points = len(stream)#[0])
    #print(n_points)
    #print('Streamline np.np.shape: {num}'.format(num=np.shape(stream)))
    for j in xrange(0, n_points):
        altered=False #we have not played around with the xyz values to make sure that they fit inside our bounding box (XXX 0 vs 1-based problem??)
        #print(j)
        # store point, convert from mm to voxel location
        x = 186-int(stream[j, 0] / float(voxelSize[0])) # XXX THIS IS A QUICK CHECK TO SEE THAT MY CODE WORKS. IT DOES, BUT YOU NEED TO THINK ABOUT TRANSFORMING THE DATA SO THAT LR is correct
        y = int(stream[j, 1] / float(voxelSize[1]))
        z = int(stream[j, 2] / float(voxelSize[2]))

        #check to see if we are outside of dimensions that are in the roiData. If so, move the voxel back until it is within it.        
        if x>=np.shape(roiData)[0]:
            x=np.shape(roiData)[0]-1
            altered=True
        if y>=np.shape(roiData)[1]:
            y=np.shape(roiData)[1]-1
            altered=True
        if z>=np.shape(roiData)[2]:
            z=np.shape(roiData)[2]-1
            altered=True
        if altered:
            pass
            print('At least one coordinate was altered')
        #print('Voxel: ' + str(x)+','+str(y)+','+str(z))
        if roiData[x, y, z] == 1:
            print('Voxel crossed at: ' + str(x)+','+str(y)+','+str(z))
            return True
        else:
            pass
    #print('No crossings of stream and roi')
    return False