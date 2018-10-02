#!/usr/bin/env python

###
# Author: Lee Parnell Thompson
# Version: 1.3.1
# 1.3.1 optimization for k==1
# 1.3: added parsing for new string class
# Disclaimer: I use these scripts for my own use, 
#	so caveat progtor. (let the programmer beware)
###

import sys,os,getopt,re,random
import time
import shutil ## copy

## Make unix pipe commands work w/o errors
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def usage(out):
	print >> out, "Usage: "
	print >> out, "    -k <int>"
	print >> out, "    -t <datatype> : default vector"
	print >> out, "         legal options: vector fasta string"
	print >> out, "    -o <directory name> : default is location of the data in directory called splits"
	print >> out, "Example:"
	print >> out, "    ./split_data.py -k 6 /location/of/some/data"

######### COMMAND LINE ARGUMENTS ##########
try:
	opts, args = getopt.gnu_getopt(sys.argv[1:], "hn:t:%:o:k:", )
except getopt.GetoptError, err:
	print >> sys.stderr, err
	usage(sys.stderr)
	sys.exit(2)

if (len(sys.argv) - len(opts) <= 1):
	usage(sys.stderr)
	sys.exit(1)
try:
	os.path.exists(sys.argv[-1])
except IOError:
	print >> sys.stderr, "No File Exists: " + sys.argv[-1]		   

########## PROGRAM VARIABLES ########
infile = sys.argv[-1]
k = 5
n = sys.maxint
nperfile = 0
whichfile = 0
remainder = 0
prev = 0
flop = False
t = "vector"
f = None
basename = os.path.basename(infile)
dirname = "%s/splits" %os.path.dirname(infile)
header = None
dim = None
o = None

PT_BEGIN_FASTA = re.compile("^>")

## Try to be a little smart and try to determine file type beforehand
for line in open(infile):
	if PT_BEGIN_FASTA.match(line): t = "fasta"
	break

for o, a in opts:
	if o in ("-h", "--help"):
		usage(sys.stdout)
		sys.exit()
	elif o == "-n": n = int(a)
	elif o == "-k": k = int(a)
	elif o == "-t": t = a
	elif o == "-o": dirname = a

#### PROGRAM VARIABLES PART 2 #######
if dirname != "": dirname += "/"
if not os.path.exists(dirname):
	os.makedirs(dirname)

if k == 1:
    outfile ="%s/split_0_%s"%(dirname, basename)
    if not os.path.exists(outfile):
        shutil.copy2(infile, outfile)
    exit(0)

## Vector Class
class Vector:
	def __init__(self, points):
		self.points = points

	def __str__(self):
		return ' '.join( self.points)

## Sequence Class
class Sequence:
	def __init__(self):
		self.id = ""
		self.seq = ""

	def __str__(self):
		return self.id + "\n" + self.seq.rstrip('/n')
	
def printIt(c, data):
	f.write(data.__str__() + "\n")

def incrementLine(c):
	global f,whichfile,prev,nperfile
	tr = min(whichfile, remainder)
	tn = whichfile - tr
	if c >= (tn * nperfile) + (tr * (nperfile +1)):
		# print "c =%d" %c
		f = open(dirname + "split_" + str(whichfile) + "_" + basename , "w")
		if header: ## write out vector header data
			nper = nperfile
			if whichfile < remainder: nper +=1
			f.write("%s %d %s\n" %(dim,nper,o)) 
		whichfile +=1

def parseFasta(infile):
	global nperfile, remainder,f
	sequence = None
	line_count = 0
	fasta_count = 0

	### Find the number of fasta points

	for line in open(infile):
		if re.match(PT_BEGIN_FASTA,line):
			fasta_count +=1
	np = min(fasta_count,n)
	nperfile = np / k
	remainder = np - (nperfile *k)
	#print n
	#print "remainder %d" %(remainder)
	#print fasta_count
	#print nperfile
	#print k
	#print np
	### Sample from the points
	fasta_count = -1
	for line in open(infile):
		line_count += 1
		## Match the id or sequence
		if PT_BEGIN_FASTA.match(line):
			fasta_count += 1
			if fasta_count >= np: 
				break
			if not sequence == None:
				f.write("%s\n" %sequence.seq )
			incrementLine(fasta_count)
			f.write(line)
			sequence = Sequence()
			sequence.id = line.strip()
		else:
			sequence.seq += line.strip()
	if sequence and fasta_count < np:
		f.write(line)

def parseVector(infile):
	global nperfile, remainder,header,dim,o
	line_count = -2
	np = sys.maxint
	for line in open(infile):
		line_count +=1
		if line_count >= np:
			break
		if line_count == -1:
			dim, np, o = line.split()
			np = min (int(np),n)
			nperfile = np / k
			remainder =  np - (nperfile*k)
			# print "np=%d nperfile=%d remainder=%d k=%d" %(np, nperfile, remainder, k)
			header = True
		else:
			incrementLine(line_count)
			f.write("%s\n" %line.strip())

def parseString(infile):
	global nperfile, remainder,f
	sequence = None
	line_count = 0

	### Find the number of fasta points
	for line in open(infile):
		line_count +=1
	np = min(line_count,n)
	nperfile = np / k
	remainder = np - (nperfile *k)
	line_count = -1
	for line in open(infile):
		line_count += 1
		incrementLine(line_count)
		f.write("%s\n" %line.strip())

### Main program
if t == "vector":
	parseVector(infile)
elif t == "fasta":
	parseFasta(infile)
elif t == "string":
	parseString(infile)
	
f.close()
