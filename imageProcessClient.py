import numpy as np
import h5py
from scipy.ndimage.filters import median_filter

def circle_region(image=None, center=(-1,-1), rmax=10, rmin=0, size=(100,100)):
	"""
	input an image, throw away any value out of [rmin, rmax]: set those values to zero
	"""
	if image is None: image = np.ones(size)
	(nx,ny) = image.shape
	(cx,cy) = (center[0], center[1])
	if center[0]==-1: cx=(nx-1.)/2.
	if center[1]==-1: cy=(ny-1.)/2.
	x = np.arange(nx) - cx
	y = np.arange(ny) - cy
	[xaxis, yaxis] = np.meshgrid(x,y)
	xaxis = xaxis.T
	yaxis = yaxis.T
	r = xaxis**2+yaxis**2
	index = np.where(r < rmin**2)
	image[index] = 0.
	index = np.where(r > rmax**2)
	image[index] = 0.
	return image

def solid_angle_correction(image, Geo):
	detDistance = Geo['detDistance']
	pixelSize   = Geo['pixelSize']
	center = Geo['center']

	(nx, ny) = image.shape
	x = np.arange(nx) - center[0]
	y = np.arange(ny) - center[1]
	[xaxis, yaxis] = np.meshgrid(x, y)
	xaxis = xaxis.T.ravel()
	yaxis = yaxis.T.ravel()
	zaxis = np.ones(nx*ny)*detDistance/pixelSize
	norm = np.sqrt(xaxis**2 + yaxis**2 + zaxis**2)
	ascale = zaxis/norm**3
	ascale /= np.amax(ascale)
	ascale.shape = (nx,ny)
	return ascale

def polarization_correction(image, Geo):
	detDistance  = Geo['detDistance']
	pixelSize    = Geo['pixelSize']
	polarization = Geo['polarization']
	center = Geo['center']

	(nx, ny) = image.shape
	x = np.arange(nx) - center[0]
	y = np.arange(ny) - center[1]
	[xaxis, yaxis] = np.meshgrid(x, y)
	xaxis = xaxis.T.ravel()
	yaxis = yaxis.T.ravel()
	zaxis = np.ones(nx*ny)*detDistance/pixelSize
	norm = np.sqrt(xaxis**2 + yaxis**2 + zaxis**2)
	
	if polarization=='x': pscale = (yaxis**2+zaxis**2)/norm**2
	elif polarization=='y': pscale = (xaxis**2+zaxis**2)/norm**2
	else: pscale = np.ones(image.shape)
	pscale /= np.amax(pscale)
	pscale.shape = (nx,ny)
	return pscale

def remove_peak_alg1(img, mask=None, sigma=15, cwin=(11,11)):
	"""
	First throw away \pm sigma*std. Second throw away \pm sigma*std
	"""
	if mask is None: mask=np.ones(img.shape)
	image = img*mask
	median = median_filter(image, cwin)*mask
	submedian = image - median
	Tindex = np.where(mask==1)
	Findex = np.where(mask==0)
	ave = np.mean(submedian[Tindex])
	std = np.std( submedian[Tindex])
	index = np.where((submedian>ave+std*sigma)+(submedian<ave-std*sigma)==True)
	image[index] = -1
	submedian[index] = 0
	ave = np.mean(submedian[Tindex])
	std = np.std( submedian[Tindex])
	index = np.where((submedian>ave+std*sigma)+(submedian<ave-std*sigma)==True)
	image[index] = -1
	image[Findex] = -1
	return image

def remove_peak_alg2(img, mask=None, thr=(None, None), cwin=(11,11)):
	"""
	Use a simple cut off method
	"""
	if mask is None: mask=np.ones(img.shape)
	image = img*mask
	median = median_filter(image, cwin)*mask
	submedian = image - median

	if thr[0] is not None:
		index = np.where(submedian<thr[0])
		image[index] = -1
	if thr[1] is not None:
		index = np.where(submedian>thr[1])
		image[index] = -1
	return image

def medianf(image, mask=1., window=(5,5)):
	median = median_filter(image, window)*mask

def meanf(image, mask=None, window=(5,5)):
	(nx,ny) = image.shape
	if mask is None: mask = np.ones(image.shape)
	ex = (window[0]-1)/2
	ey = (window[1]-1)/2
	sx = ex*2+1
	sy = ey*2+1
	Data = np.zeros((sx*sy, nx+ex*2, ny+ey*2));
	Mask = np.zeros(data.shape);

	for i in range(sx):
		for j in range(sy):
			Data[i*sy+j, i:(i+nx), j:(j+ny)] = image.copy()
			Mask[i*sy+j, i:(i+nx), j:(j+ny)] = mask.copy()

	Mask = np.sum(Mask, axis=0);
	Data = np.sum(Data, axis=0);
	index = np.where(Mask>0);
	Data[index] /= Mask[index]
	return Data