import time
import os, sys
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-i","--i", help="save folder", default=".", type=str)
args = parser.parse_args()

tic = time.time()
print args.i
if args.i == '.' or not os.path.isfile(args.i):
	toc = time.time()
	print "###"+str(toc-tic).rjust(5)+"   "+ "### no such file"
	raise Exception('no such file')
print "hahaha"