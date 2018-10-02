#!/usr/bin/env python
#Version 1.4

import sys,os,re,getopt
from subprocess import *
## Make unix pipe commands work w/o errors
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

## Define constants
data_dir = "/Users/parnell/data" ## our data directory must be absolute 
# orig_data_file = "%s/nasa.vec" %data_dir  ## our data file
# query_file = "%s/nasa_query.vec" %data_dir ## our query file
#orig_data_files = ["%s/gaussian-20-1-1000000.tau=0.0691588.vec" %data_dir, "%s/gaussian-20-1-1000000.tau=0.138318.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.207477.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.276635.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.345794.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.414953.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.484112.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.553271.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.62243.vec" %data_dir,"%s/gaussian-20-1-1000000.tau=0.691588.vec" %data_dir]  ## our data file
# orig_data_files =["%s/gaussian-1-1-1000000.tau=0.0599312.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.119862.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.179793.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.239725.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.299656.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.359587.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.419518.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.479449.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.53938.vec" %data_dir,"%s/gaussian-1-1-1000000.tau=0.599312.vec" %data_dir, "%s/gaussian-1-1-1000000.tau=0.vec" %data_dir,]

# orig_data_files = ["%s/gaussian_1_5_0.8_1000000.vec" %data_dir]
# query_file = "%s/gaussian_query_1_5_0.8_100.vec" %data_dir ## our query file

bprog = "build-sat-vectors"  #specify the prog to use
qprog = "query-sat-vectors"  #specify the query prog to use
rstart= 0.4   ## radius start
rstep= 0.1   ## radius step
rlimit=0.4    ## radius end
ntrees = [1]  ## Number of trees created
# variances = ["0.01", "0.1", "0.2","0.3","0.4","0.5","0.6","0.7","0.8"]
# sizes = ["10000","100000","10000000"]
dims = ["1"]
loopArray=dims
index_num =0
for i in range(len(loopArray)):
    index_num+=1
    # orig_data_file = "%s/gaussian_1_5_0.1_%s.vec" %(data_dir,sizes[i])
    # query_file = "%s/gaussian_query_1_5_0.1_%s_100.vec" %(data_dir,sizes[i]) ## our query file
    orig_data_file = "%s/gaussian_nclus=5_dim=5_var=0.1_size=1000000.vec" %(data_dir)
    query_file = "%s/queries/gaussian-query-1_nclus=5_dim=5_var=0.1_size=1000000.vec" %(data_dir) ## our query file

    orig_index_name="%d_dim_sat" %index_num
    
    ## Other constants
    run_sisap_prog = "run_sisap.py"
    split_prog = "splitdata.py"
    convert_prog = "convertcoords"
    orig_data_basename =  os.path.basename(orig_data_file)
    rcfile = "%s-row-column.txt" %orig_index_name

    orig_output_dir = "%s_output" %orig_index_name
    index_dir = "%s/indexes" %orig_output_dir
    split_dir = "%s/splits" %orig_output_dir

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
    print "building index '%s'  datatype='%s'" %(orig_data_file, datatype)

    ## Write the number of trees
    rcf = open("%s/%s" %(orig_output_dir,rcfile),"w")
    for nt in ntrees:
        rcf.write("\t%d" %nt)
    rcf.write("\n")
    rcf.close()


    ## for each of the specified trees
    for nt in ntrees:
        nt = int(nt)
        print "############################## %d" %nt
        ### Create our data and index directories
        psplit_dir = "%s_%d" %(split_dir,nt)
        pindex_dir = "%s_%d" %(index_dir,nt)
        if not os.path.exists(psplit_dir):
            os.makedirs(psplit_dir)
        if not os.path.exists(pindex_dir):
            os.makedirs(pindex_dir)
    
        ### Split data into nt parts
        cmdstr = "%s -o %s -k %d %s" %(split_prog,psplit_dir,nt,orig_data_file)
        print cmdstr
        retcode = call(cmdstr, shell=True)
        poutput_loc = "%s/%d_%s" %(orig_output_dir,nt,orig_index_name)
    
        ### Data must now be converted to Sisap format
        for i in range(0,nt):
            psplit_name = "split_%d_%s" %(i,orig_data_basename)
            if datatype == "vectors":
                psplit_bin = "%s.bin"  %(psplit_name)
                pdata_file = "%s/%s" %(psplit_dir,psplit_bin)
                cmdstr = "%s '%s/%s' '%s'" %(convert_prog,psplit_dir,psplit_name, pdata_file)
                if i==0 or i==nt-1: print ">%s" %cmdstr
                retcode = call(cmdstr, shell=True)  
            else :
                pdata_file = "%s/%s" %(psplit_dir, psplit_name)
        
        
            ### Now we can run sisap.py on each of the splits
            pindex_name="%d_%s" %(i,orig_index_name)
            pquery_file = query_file
            cmdstr = "%s --index-name=%s --data-file=%s --index-dir=%s --query-file=%s --sisap-build=%s --sisap-query=%s --output-loc=%s --rstart=%f --rstep=%f --rlimit=%f" \
                %(run_sisap_prog,pindex_name,pdata_file,pindex_dir,query_file,bprog,qprog,poutput_loc, rstart, rstep, rlimit)
            if i==0 or i==nt-1: print ">%s" %cmdstr
            retcode = call(cmdstr, shell=True)  
        
        

