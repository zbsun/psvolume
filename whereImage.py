"""
run this script: mpirun -n 10 python whereImage.py --o /reg/neh/home/zhensu --num 1000

If the output "--o" folder is not specified, then it will save to the current path

--xds should be a file path 
"""
from userScript import *
from xdsIndexingFile import *
from fileManager import *
from imageProcessClient import *
from mpi4py import MPI
comm_rank = MPI.COMM_WORLD.Get_rank()
comm_size = MPI.COMM_WORLD.Get_size()
zf = iFile()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-o","--o", help="save folder", default="", type=str)
parser.add_argument("-fname","--fname", help="input files", default=".", type=str)
parser.add_argument("-xds","--xds", help="xds file", default=".", type=str)
parser.add_argument("-num","--num", help="num of images to process", default=-1, type=int)
args = parser.parse_args()


if not (args.o).endswith('/'): args.o = args.o+'/'
path = args.o[0:(len(args.o)-args.o[::-1].find('/',1))];
folder = args.o


# computation
if args.xds != ".":
	print "### xds file imported: ", args.xds
	Geo = {}; Bmat = None; invBmat = None;  invAmat = None
	[Geo, Bmat, invBmat, invAmat] = user_get_xds(args.xds)


if comm_rank == 0:
	print "### save to path: ", path
	print "### save to folder: ", folder
	if not os.path.exists(folder):
		os.mkdir(folder)
else:
	while not os.path.exists(folder): pass


Smat = Bmat*1.0/np.sqrt(np.sum(Bmat[:,1]**2))
if args.fname != '.': fname = args.fname.replace('#####', str(1).zfill(5))
else: fname=None
mask = user_get_mask(Geo, fname=fname)
Mask = expand_mask(mask, cwin=(2,2), value=0)


if comm_rank == 0:
	Filename = path+'/image.process'
	zf.h5writer(Filename, 'mask', mask)
	zf.h5modify(Filename, 'Mask', Mask)
	zf.h5modify(Filename, 'Bmat', Bmat)
	zf.h5modify(Filename, 'invBmat', invBmat)

#raise Exception('error')

sep = np.linspace(0, args.num, comm_size+1).astype('int')
for idx in range(sep[comm_rank], sep[comm_rank+1]):
	if args.fname != '.': 
		fname = args.fname.replace('#####', str(idx+1).zfill(5))
	image = user_get_image(idx, fname = fname)
	image[np.where(image>10000)] = -1
	image[np.where(image<0)] = -1

	quaternion = user_get_orientation(idx, increment=Geo['Angle_increment'])
	R1 = Quat2Rotation(quaternion)
	if invAmat is None: matrix = invBmat.dot(invUmat.dot(R1))
	else: matrix = invAmat.dot(R1)

	fsave = folder + '/'+str(idx).zfill(5)+'.slice'
	zf.h5writer(fsave, 'readout', 'image')
	zf.h5modify(fsave, 'image', image*mask)
	zf.h5modify(fsave, 'center', Geo['center'])
	zf.h5modify(fsave, 'exp', False)
	zf.h5modify(fsave, 'run', False)
	zf.h5modify(fsave, 'event', False)
	zf.h5modify(fsave, 'waveLength', Geo['wavelength'])
	zf.h5modify(fsave, 'detDistance', Geo['detDistance'])
	zf.h5modify(fsave, 'pixelSize', Geo['pixelSize'])
	zf.h5modify(fsave, 'polarization', Geo['polarization'])
	zf.h5modify(fsave, 'rot', 'matrix')
	zf.h5modify(fsave, 'rotation', matrix)
	zf.h5modify(fsave, 'scale', user_get_scalingFactor(idx))
	zf.h5modify(fsave, 'Smat', Smat)
	print '### Rank: '+str(comm_rank).rjust(3)+' finished image:  '+str(sep[comm_rank])+'/'+str(idx)+'/'+str(sep[comm_rank+1])
	if idx>4000: break