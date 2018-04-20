from mpidata import *
from FileManager import *
from ImageMergeClient import *
import argparse
comm_rank = MPI.COMM_WORLD.Get_rank()
comm_size = MPI.COMM_WORLD.Get_size()
parser = argparse.ArgumentParser()
parser.add_argument("-i","--i", help="raw file folder", default="/", type=str)
parser.add_argument("-o","--o", help="save folder", default="/", type=str)
parser.add_argument("-num","--num", help="num of images to process", default=-1, type=int)
args = parser.parse_args()

zf = iFile()
if num==-1:	num = zf.counterFile(args.i, title='.slice')
else: num = int(args.num)
fsave = zf.newfolder(args.o, title='sp')

Vol = {}
Vol['volumeCenter'] = 240
Vol['volumeSampling'] = 4
Vol['volumeSize'] = 2*Vol['volumeCenter']+1
model3d = np.zeros([Vol['volumeSize']]*3)
weight  = np.zeros([Vol['volumeSize']]*3)

if comm_rank == 0:
	for nrank in range(comm_size-1):
		md=mpidata()
		md.recv()
		model3d += md.model3d
		weight += md.weight
		recvRank = md.small.rank
		md = None
		print '### received file from ' + str(recvRank).rjust(2)

	model3d = ModelScaling(model3d, weight)
	pathIntens = fsave+'/merge.volume'
	zf.writer(pathIntens, 'intens', model3d, chunks=(1, Vol['volumeSize'], Vol['volumeSize']), opt=7)
	zf.modify(pathIntens, 'weight', weight,  chunks=(1, Vol['volumeSize'], Vol['volumeSize']), opt=7)

else:
	sep = np.linspace(0, num, comm_size).astype('int')
	for idx in range(sep[comm_rank-1], sep[comm_rank]):
		fname = os.path.join(args.i, 'mergeImage_'+str(idx).zfill(5)+'.slice')
		image = zf.h5reader(fname, 'image')
		Geo = zf.get_image_info(fname)
		[model3d, weight] = ImageMerge(model3d, weight, image, Geo, Vol)

	print '### rank ' + str(comm_rank).rjust(2) + ' is sending file ... '

	md=mpidata()
	md.addarray('model3d', model3d)
	md.addarray('weight', weight)
	md.small.rank = comm_rank
	md.send()
	md = None