# -*- coding: utf-8 -*-
"""
Christopher J. Steele
Created on Sat Mar 15 14:21:52 2014

Used code from Satra/Chris at https://github.com/nipy/nipype/blob/master/nipype/interfaces/mrtrix/convert.py

"""

# -*- coding: utf-8 -*-
import os.path as op
import nibabel as nb, nibabel.trackvis as trk
import numpy as np
from nibabel.trackvis import HeaderError
from nibabel.volumeutils import native_code
from dipy.tracking.utils import move_streamlines, affine_from_fsl_mat_file

#from ..base import (TraitedSpec, BaseInterface, BaseInterfaceInputSpec,
#                    File, isdefined, traits)
#from ...utils.filemanip import split_filename
#from ...utils.misc import package_check
#from ...workflows.misc.utils import get_data_dims, get_vox_dims

#import warnings
#have_dipy = True
#try:
#    package_check('dipy')
#except Exception, e:
#    False
#else:
#    from dipy.tracking.utils import move_streamlines, affine_from_fsl_mat_file
#
#from nibabel.orientations import aff2axcodes
#
#from ... import logging
#iflogger = logging.getLogger('interface')

#%%
def transform_to_affine(streams, header, affine):
	rotation, scale = np.linalg.qr(affine)
	streams = move_streamlines(streams, rotation)
	scale[0:3,0:3] = np.dot(scale[0:3,0:3], np.diag(1./header['voxel_size']))
	scale[0:3,3] = abs(scale[0:3,3])
	streams = move_streamlines(streams, scale)
	return streams

def read_mrtrix_tracks(in_file, as_generator=True):
	header = read_mrtrix_header(in_file)
	streamlines = read_mrtrix_streamlines(in_file, header, as_generator)
	return header, streamlines

def read_mrtrix_header(in_file):
    fileobj = open(in_file,'r')
    header = {}
    iflogger.info('Reading header data...')
    for line in fileobj:
        if line == 'END\n':
            iflogger.info('Reached the end of the header!')
            break
        elif ': ' in line:
            line = line.replace('\n','')
            line = line.replace("'","")
            key  = line.split(': ')[0]
            value = line.split(': ')[1]
            header[key] = value
            iflogger.info('...adding "{v}" to header for key "{k}"'.format(v=value,k=key))
    fileobj.close()
    header['count'] = int(header['count'].replace('\n',''))
    header['offset'] = int(header['file'].replace('.',''))
    return header

def read_mrtrix_streamlines(in_file, header, as_generator=True):
    offset = header['offset']
    stream_count = header['count']
    fileobj = open(in_file,'r')
    fileobj.seek(offset)
    endianness = native_code
    f4dt = np.dtype(endianness + 'f4')
    pt_cols = 3
    bytesize = pt_cols*4
    def points_per_track(offset):
        n_streams = 0
        n_points = 0
        track_points = []
        iflogger.info('Identifying the number of points per tract...')
        all_str = fileobj.read()
        num_triplets = len(all_str)/bytesize
        pts = np.ndarray(shape=(num_triplets,pt_cols), dtype='f4',buffer=all_str)
        nonfinite_list = np.where(np.isfinite(pts[:,2]) == False)
        nonfinite_list = list(nonfinite_list[0])[0:-1] # Converts numpy array to list, removes the last value
        nonfinite_list_bytes = [offset+x*bytesize for x in nonfinite_list]
        for idx, value in enumerate(nonfinite_list):
            if idx == 0:
                track_points.append(nonfinite_list[idx])
            else:
                track_points.append(nonfinite_list[idx]-nonfinite_list[idx-1]-1)
        return track_points, nonfinite_list

    def track_gen(track_points):
        n_streams = 0
        iflogger.info('Reading tracks...')
        while True:
            n_pts = track_points[n_streams]
            pts_str = fileobj.read(n_pts * bytesize)
            nan_str = fileobj.read(bytesize)
            if len(pts_str) < (n_pts * bytesize):
                if not n_streams == stream_count:
                    raise HeaderError(
                        'Expecting %s points, found only %s' % (
                                stream_count, n_streams))
                    iflogger.error('Expecting %s points, found only %s' % (
                                stream_count, n_streams))
                break
            pts = np.ndarray(
                shape = (n_pts, pt_cols),
                dtype = f4dt,
                buffer = pts_str)
            nan_pt = np.ndarray(
                shape = (1, pt_cols),
                dtype = f4dt,
                buffer = nan_str)
            if np.isfinite(nan_pt[0][0]):
                raise ValueError
                break
            xyz = pts[:,:3]
            yield xyz
            n_streams += 1
            if n_streams == stream_count:
                iflogger.info('100% : {n} tracks read'.format(n=n_streams))
                raise StopIteration
            if n_streams % (float(stream_count)/100) == 0:
                percent = int(float(n_streams)/float(stream_count)*100)
                iflogger.info('{p}% : {n} tracks read'.format(p=percent, n=n_streams))
    track_points, nonfinite_list = points_per_track(offset)
    fileobj.seek(offset)
    streamlines = track_gen(track_points)
    if not as_generator:
        streamlines = list(streamlines)
    return streamlines