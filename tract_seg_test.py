
# In[1]:

import os
working_dir="/scr/alaska2/steele/Projects/Working/7T/CBTractography/processing/dmri_mrtrix_dti/dwiproc/tractography/_id_BK1T/probCSDstreamtrack"

files = get_ipython().getoutput(u'ls *TDI_0*')
files = ['HIV_TDI_0p2.nii.gz','HV_TDI_0p2.nii.gz','HVI_TDI_0p2.nii.gz','crusI_TDI_0p2.nii.gz','crusII_TDI_0p2.nii.gz']
#files = ['HIV_TDI_0p05.nii.gz','HV_TDI_0p05.nii.gz','HVI_TDI_0p05.nii.gz','crusI_TDI_0p05.nii.gz','crusII_TDI_0p05.nii.gz']


# In[2]:

#files.insert(0,files[0]) #padd with the first volume so that segmentation is 1-based and 0s for mask
files


# Out[2]:

#     ['HIV_TDI_0p2.nii.gz',
#      'HV_TDI_0p2.nii.gz',
#      'HVI_TDI_0p2.nii.gz',
#      'crusI_TDI_0p2.nii.gz',
#      'crusII_TDI_0p2.nii.gz']

# In[4]:

import numpy as np
np.concatenate((np.zeros((2,2))[...,np.newaxis], np.ones((2,2))[...,np.newaxis]), axis=2)
import nibabel as nb
data_list = [nb.load(fn).get_data()[...,np.newaxis] for fn in files] #load all of the files


# In[5]:

combined = np.concatenate(data_list, axis=-1) #concatenate all of the input data
combined.shape


# Out[5]:

#     (100, 128, 76, 5)

# In[8]:

hard_seg =combined.argmax(axis=-1)+1 #now we have a 1-based segmentation (largest number in each voxel)
hard_seg[combined.std(axis=-1) == 0] = 0 #where there is no difference between volumes, this should be the mask, set to 0



# In[9]:

#save
nii = nb.load(files[0])
new_nii = nb.Nifti1Image(hard_seg, nii.get_affine(), nii.get_header())
new_nii.to_filename("TDI_DN_hard_seg_bin_0p2.nii.gz")


# In[10]:

#np.shape(hard_seg==idx)


# Out[10]:


    ---------------------------------------------------------------------------
    NameError                                 Traceback (most recent call last)

    <ipython-input-10-a2f955bf7bf6> in <module>()
    ----> 1 np.shape(hard_seg==idx)
    

    NameError: name 'idx' is not defined


# In[29]:

# create soft segmentation to show strength of the dominant tract in each voxel
seg_part = np.zeros_like(hard_seg)
seg_temp = np.zeros_like(hard_seg)
seg_total = combined.sum(axis=-1)

idx=1
for seg in files:
    seg_temp = combined[:,:,:,idx-1] #get value at this voxel for this tract seg (-1 for 0-based index of volumes)
    seg_part[hard_seg==idx] = seg_temp[hard_seg==idx] #1-based index of segmentation
    idx +=1

#seg_pct = seg_part/seg_total
seg_pct = np.where(seg_part>0, seg_part/seg_total,0) #where there is a zero (regions with no tracts) return 0, otherwise do the division



# In[30]:

#convert so that each segmentation goes from above its segmented to number to just below +1
#.001 added to make sure that segmentations where tracts are 100% do not push into the next segmentation (not necessary depending on how the images are displayed)
#1st is 1-1.999, 2nd is 2-3.... (though the values should always be above the integer b/c of the segmentation
seg_pct=np.subtract(np.add(seg_pct,hard_seg),.001) #add them and subtract a value, now the values are percentages of the segmentations for each number


# In[31]:

#save proportion image
#new_nii = nb.Nifti1Image(seg_total, nii.get_affine(), nii.get_header())
#new_nii.to_filename("TDI_DN_hard_seg_tot_0p2.nii.gz")
#new_nii = nb.Nifti1Image(seg_part, nii.get_affine(), nii.get_header())
#new_nii.to_filename("TDI_DN_hard_seg_part_0p2.nii.gz")


new_nii = nb.Nifti1Image(seg_pct, nii.get_affine(), nii.get_header())
new_nii.to_filename("TDI_DN_hard_seg_pct_0p2.nii.gz")


# In[165]:




# In[166]:




# In[126]:




# In[ ]:



