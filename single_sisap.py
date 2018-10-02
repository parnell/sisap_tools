#!/usr/bin/env python3
#Version 1.4
from __future__ import print_function
import sys,os,re,getopt
from subprocess import *
## Make unix pipe commands work w/o errors
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

# genGaussData.py ${NCLUS} ${DIM} ${VAR} ${SIZE} gauss ${FOLD} ${QSIZE}
#gaussian-nclus=${NCLUS}_dim=${DIM}_var=${VAR}_size=${SIZE}.hdf5
#${VGDATA}/queries/gaussian-query-1_nclus=${NCLUS}_dim=${DIM}_var=${VAR}_size=${SIZE}.hdf5
## Define constants
def usage(out):
	print("Usage: ./single_sisap.py <nclusters> <dimensions> <variance> <size> <radius> <numQueryFiles> <index type>", file=sys.stderr)

if (len(sys.argv) < 6):
	usage(sys.stderr)
	sys.exit(2)
useSimpleQueries = False
nclus = int(sys.argv[-7])    # numero de clusters
dim =   int(sys.argv[-6])    # la dimension de los vectores
var =   sys.argv[-5];    # la varianza (devstd^2)
size = int(sys.argv[-4])
radius = float(sys.argv[-3])
nQueryFiles = int(sys.argv[-2])
indexType = sys.argv[-1]

dataDir = "/Users/parnell/data"
queryPath = "%s/queries" %dataDir

i = 1
baseDataName = "gaussian_nclus=%d_dim=%d_var=%s_size=%d" %(nclus,dim,var,size)
dataName = "%s.vec" %(baseDataName)
orig_data_file = "%s/%s" %(dataDir,dataName)
queryFile = "%s/gaussian-query-%d_nclus=%d_dim=%d_var=%s_size=%d.vec" %(queryPath,i,nclus,dim,var,size)

# orig_data_files = ["%s/gaussian_1_5_0.8_1000000.vec" %dataDir]
# query_file = "%s/gaussian_query_1_5_0.8_100.vec" %dataDir ## our query file

bprog = "build-%s-vectors"  %indexType #specify the prog to use
qprog = "query-%s-vectors"  %indexType #specify the query prog to use
rstart= radius   ## radius start
rstep= radius   ## radius step
rlimit=radius    ## radius end
ntrees = [1]  ## Number of trees created
loopArray = ntrees
# variances = ["0.01", "0.1", "0.2","0.3","0.4","0.5","0.6","0.7","0.8"]
# sizes = ["10000","100000","10000000"]

index_num =0
index_num+=1
# orig_data_file = "%s/gaussian_1_5_0.1_%s.vec" %(dataDir,sizes[i])
# query_file = "%s/gaussian_query_1_5_0.1_%s_100.vec" %(dataDir,sizes[i]) ## our query file

orig_index_name="%s_%d_%d_%s_%d_%d_dim" %(indexType, nclus, dim, var, size, index_num)

## Other constants
run_sisap_prog = "run_sisap.py"
split_prog = "splitdata.py"
convert_prog = "convertcoords"
orig_data_basename =  os.path.basename(orig_data_file)
rcfile = "%s-row-column.txt" %orig_index_name

orig_output_dir = "%s_output" %orig_index_name
index_dir = "%s/indexes" %orig_output_dir
split_dir = "%s/%s_splits" %(dataDir,baseDataName)

orig_results_file = "%s-results.txt" %orig_index_name
rcfile = "%s-column.txt" %orig_index_name
PT_RESULT = re.compile("Total distances per query: ([^ ]+)$")
PT_BEGIN_FASTA = re.compile("^>")

## make the output directory if it doesnt exist
if not os.path.exists(orig_output_dir):
    os.makedirs(orig_output_dir)

## Find datatype
datatype = "vectors"
for line in open(orig_data_file):
    if PT_BEGIN_FASTA.match(line): datatype = "fasta"
    break
print( "building index '%s'  datatype='%s'" %(orig_data_file, datatype))

## Write the number of trees
rcf = open("%s/%s" %(orig_output_dir,rcfile),"w")
for nt in loopArray:
    rcf.write("\t%d" %nt)
rcf.write("\n")
rcf.close()


## for each of the specified trees
for nt in loopArray:
    nt = int(nt)
    print( "############################## %d" %nt)
    ### Create our data and index directories
    psplit_dir = "%s_%d" %(split_dir,nt)
    pindex_dir = "%s_%d" %(index_dir,nt)
    if not os.path.exists(psplit_dir):
        os.makedirs(psplit_dir)
    if not os.path.exists(pindex_dir):
        os.makedirs(pindex_dir)

    ### Split data into nt parts
    cmdstr = "%s -o %s -k %d %s" %(split_prog,psplit_dir,nt,orig_data_file)
    print( cmdstr)
    retcode = call(cmdstr, shell=True)
    poutput_loc = "%s/%d_%s" %(orig_output_dir,nt,orig_index_name)

    ### Data must now be converted to Sisap format
    for i in range(0,nt):
        dt = "--data-type=string"
        psplit_name = "split_%d_%s" %(i,orig_data_basename)
        if datatype == "vectors":
            dt = "--data-type=vector"
            psplit_bin = "%s.bin"  %(psplit_name)
            pdata_file = "%s/%s" %(psplit_dir,psplit_bin)
            cmdstr = "%s '%s/%s' '%s'" %(convert_prog,psplit_dir,psplit_name, pdata_file)
            if i==0 or i==nt-1: print( ">%s" %cmdstr)
            if not os.path.exists(pdata_file):
                retcode = call(cmdstr, shell=True)  
            elif i==0 or i==nt-1:
                print("convertcoords: skipped because file already exists")  
        else :
            pdata_file = "%s/%s" %(psplit_dir, psplit_name)
    
    
        ### Now we can run sisap.py on each of the splits
        pindex_name="%d_%s" %(i,orig_index_name)
        pquery_file = queryFile
        sim = "--simple" if useSimpleQueries else ""
        cmdstr = "%s %s --index-name=%s --data-file=%s --index-dir=%s --query-file=%s --sisap-build=%s --sisap-query=%s --output-loc=%s --rstart=%f --rstep=%f --rlimit=%f %s" \
            %(run_sisap_prog,dt, pindex_name,pdata_file,pindex_dir,queryFile,bprog,qprog,poutput_loc, rstart, rstep, rlimit, sim)
        if i==0 or i==nt-1: print (">%s" %cmdstr)
        retcode = call(cmdstr, shell=True)  
    
    

