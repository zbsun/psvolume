import os
import numpy as np 
from mpidata import *
from fileManager import *
from imageMergeClient import *
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-i","--i", help="save folder", default=".", type=str)
parser.add_argument("-mode","--mode", help="matrix", default="hkl", type=str)
parser.add_argument("-peak","--peak", help="keep the bragg peak or not", default=0, type=int)
parser.add_argument("-vSampling","--vSampling", help="num of images to process", default=1, type=int)
parser.add_argument("-vCenter","--vCenter", help="num of images to process", default=60, type=int)
parser.add_argument("-nmin","--nmin", help="minimum image number", default=0, type=int)
parser.add_argument("-nmax","--nmax", help="maximum image number", default=-1, type=int)
args = parser.parse_args()


zf = iFile()
if not (args.i).endswith('/'): args.i = args.i+'/'
[nmax, allFile] = zf.counterFile(args.i, title='.slice')
path = args.i[0:(len(args.i)-args.i[::-1].find('/',1))];
if args.nmax != -1: nmax = int(args.nmax)

Vol = {}
Vol['volumeCenter'] = int(args.vCenter)
Vol['volumeSampling'] = int(args.vSampling)
Vol['volumeSize'] = 2*Vol['volumeCenter']+1
model3d = np.zeros([Vol['volumeSize']]*3)
weight  = np.zeros([Vol['volumeSize']]*3)
nmin = args.nmin; 


# f = h5py.File('/reg/data/ana04/users/zhensu/xpptut/experiment/0024/wtich/data-ana/scalesMike.h5')
# scaleMike = f[f.keys()[0]].value
# f.close()


if comm_rank == 0:
	fsave = zf.makeFolder(path, title='sr')

	print '### Path  : ', path
	print '### Folder: ', args.i 
	print "### Fsave : ", fsave
	print "### Images:  [", nmin, nmax, ')'
	print "### Mode  : ", args.mode
	print "### Volume: ", model3d.shape
	print "### Center: ", Vol['volumeCenter']
	print "### Sampling: ", Vol['volumeSampling']

	countImage = 0
	for nrank in range(comm_size-1):
		md=mpidata()
		md.recv()
		model3d += md.model3d
		weight += md.weight
		recvRank = md.small.rank
		countImage += md.small.num
		md = None
		print '### received file from ' + str(recvRank).rjust(2) + '/' + str(comm_size)

	model3d = ModelScaling(model3d, weight)
	pathIntens = fsave+'/merge.volume'
	if args.mode == 'xyz': Smat = np.eye(3)
	else: Smat = zf.h5reader(args.i+'/00000.slice', 'Smat')

	print "### processed image number: ", countImage
	print "### saving File: ", pathIntens
	ThisFile = zf.readtxt(os.path.realpath(__file__))
	zf.h5writer(pathIntens, 'execute', ThisFile)
	zf.h5modify(pathIntens, 'intens', model3d, chunks=(1, Vol['volumeSize'], Vol['volumeSize']), opts=7)
	zf.h5modify(pathIntens, 'weight', weight,  chunks=(1, Vol['volumeSize'], Vol['volumeSize']), opts=7)
	zf.h5modify(pathIntens, 'Smat', Smat)

else:
	sep = np.linspace(nmin, nmax, comm_size).astype('int')
	for idx in range(sep[comm_rank-1], sep[comm_rank]):
		fname = args.i+'/'+str(idx).zfill(5)+'.slice'
		image = zf.h5reader(fname, 'image')
		Geo = zf.get_image_info(fname)
		image = image * Geo['scale']

		sumIntens = round(np.sum(image), 8)
		#image = image/sumIntens*1.0e8;
		
		if args.mode=='xyz':
			moniter = 'xyz'
			[model3d, weight] = ImageMerge_XYZ(model3d, weight, image, Geo, Vol, Kpeak=args.peak)
		else:
			moniter = 'hkl'
			[model3d, weight] = ImageMerge_HKL(model3d, weight, image, Geo, Vol, Kpeak=args.peak)
		print '### rank ' + str(comm_rank).rjust(3) + ' is processing file: '+str(sep[comm_rank-1])+'/'+str(idx)+'/'+str(sep[comm_rank]) +'  sumIntens: '+str(sumIntens).ljust(10)

	print '### rank ' + str(comm_rank).rjust(3) + ' is sending file ... '
	md=mpidata()
	md.addarray('model3d', model3d)
	md.addarray('weight', weight)
	md.small.rank = comm_rank
	md.small.num = sep[comm_rank]-sep[comm_rank-1]
	md.send()
	md = None