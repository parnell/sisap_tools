#!/usr/bin/env python
#version 1.4.1

import sys,os,re,getopt
from subprocess import *
## Make unix pipe commands work w/o errors
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def usage(out):
    print( "Usage: ", file=out)
    print( "    --index-name <index name>", file=out)
    print( "    --data-file <data file> : ", file=out)
    print( "    --index-dir <index dir> : ", file=out)
    print( "    --query-file <> : ", file=out)
    print( "    --sisap-build <> : ", file=out)
    print( "    --sisap-query <> : ", file=out)
    print( "    --output-loc <> : ", file=out)
    print( "    --rstart <> : ", file=out)
    print( "    --rlimit <> : ", file=out)
    print( "    --rstep <> : ", file=out)
    print( "Example:", file=out)
    print( "    ./run_sisap.py ", file=out)


########## PROGRAM VARIABLES ########
index_name=None
data_file = None
data_type = None
index_dir = None
query_file = None
bprog = None
qprog = None
output_loc = ""
limit = None
r = rstart = 0.0
b = bstart = 3.0
rlimit = 1.0
rstep = 0.1
class DATA_TYPE:
    VECTOR = 0
    STRING = 1
simple = False
######### COMMAND LINE ARGUMENTS ##########
try:
    opts, args = getopt.gnu_getopt(sys.argv[1:], "h",\
        ("index-name=","data-file=","index-dir=","query-file=",\
        "sisap-build=","sisap-query=","output-loc=","rstart=","rlimit=",\
        "rstep=","simple", "data-type=") )
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(sys.stdout)
            sys.exit()
        elif o == "--index-name": index_name = a
        elif o == "--data-file": data_file = a
        elif o == "--index-dir": index_dir = a
        elif o == "--query-file": query_file = a
        elif o == "--sisap-build": bprog = a
        elif o == "--sisap-query": qprog = a
        elif o == "--simple": simple = True # turn on simple queries (no max,min, etc)
        elif o == "--output-loc": output_loc = a
        elif o == "--rstart": r = rstart = float(a)
        elif o == "--rlimit": rlimit = float(a)
        elif o == "--rstep": rstep = float(a)
        elif o == "--data-type": 
            if a.lower() == "string": data_type = DATA_TYPE.STRING
            elif a.lower() == "vector": data_type = DATA_TYPE.VECTOR

except getopt.GetoptError as err:
    print(err,file=sys.stderr)
    usage(sys.stderr)
    sys.exit(2)

# if (len(sys.argv) - len(opts) <= 1):
#   usage(sys.stderr)
#   sys.exit(1)

#### Program Variables part 2
if output_loc != "": output_loc += "/"
if not os.path.exists(output_loc):
    os.makedirs(output_loc)

output_dir = "%s/%s_output" %(output_loc,index_name)
results_file = "%s/%s-results.txt" %(output_dir,index_name)

PT_AVG = re.compile("Average distances per query: ([^ ]+)$")
PT_TOTAL = re.compile("Total distances: ([^ ]+)$")
PT_RESULT = re.compile("([0-9]+) objects found")
PT_CALC = re.compile("([0-9]+) calcs")
PT_REAL = re.compile("real  0m(.*)s")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

resultsf = open(results_file , "w") 
resultsf.write("\t# Results\n")

bckt_size = 3

### Build Index and write to file
indexPath ="%s/%s" %(index_dir,index_name)
cmd = ["time",bprog,data_file,"0",indexPath , str(bckt_size),"3","6"]
cmdstr = ' '.join([c for c in cmd])
print(cmdstr) ### output cmd string for clarity
if not os.path.exists(indexPath):    
    p = Popen(cmd, stdout=PIPE)
    output = p.communicate()[0]
    buildf = open("%s/build.txt" %output_dir, "w")
    buildf.write(output)
    buildf.close()
    retcode = call(cmdstr, shell=True)
else:
    print("build skipped as index already exists")
qfile = "%s/query.sisap" %output_dir


while r <= rlimit:
    print( "### calculating r=%f" %r)
    result_file = "%s/query-%f" %(output_dir, r)
    line_count=0
    qf = open(qfile, "w")
    ### Queries need to be comma separated with radius as first value
    i = 0
    for line in open(query_file):
        line_count+=1
        if limit and line_count > limit: break
        if line_count == 1 and data_type == DATA_TYPE.VECTOR: continue  ### Need to remove the header line
        line = line.replace(" ", ",")
        q = "%f,%s" %(r,line)
        qf.write(q)
        if not simple:
            iqfile = "%s/query.%d.sisap" %(output_dir, i)
            iqf = open(iqfile,"w")
            iqf.write(q)
        i+=1
    qf.write("-0\n")
    qf.close()
    ## Query indices
    try:
        if not simple:
            for i in range(line_count):
                iqfile = "%s/query.%d.sisap" %(output_dir, i)
                cmdstr = "(time %s %s/%s) < %s 1<&-  2>> %s " %(qprog,index_dir,index_name, iqfile , result_file)
                # print(cmdstr)
                retcode = call(cmdstr, shell=True)

                if retcode < 0:
                    print  ("Child was terminated by signal %d" %retcode, file=stderr)
                    sys.exit(1)
                else:
                    # print >>sys.stderr, "Child returned", retcode
                    pass
        else:
            cmdstr = "(time %s %s/%s) < %s 1<&-  2>> %s " %(qprog,index_dir,index_name, query_file , result_file)
            print(cmdstr)
            retcode = call(cmdstr, shell=True)
        
    except OSError as e:
        print ("Execution failed:", e, file=stderr)
        sys.exit(1)

    nresults = 0.0
    sumresults = 0.0
    ## Merge query results into one file
    for line in open(result_file):
        m = PT_CALC.match(line)
        if m : 
            resultsf.write("r=" + str(r) + "\tcalc=" + m.group(1) + "\n")
        m = PT_RESULT.match(line)
        if m : 
            nresults += 1
            sumresults += int(m.group(1))
        m = PT_TOTAL.match(line)
        if m : 
            resultsf.write("r=" + str(r) + "\ttotal_calcs=" + m.group(1))
        m = PT_AVG.match(line)
        if m : 
            resultsf.write("r=" + str(r) + "\tavg_calcs=" + m.group(1))
        m = PT_REAL.match(line)
        if m : 
            resultsf.write("r=" + str(r) + "\ttime=" + m.group(1) +"\n")
    if nresults == 0: 
        nresults = float('nan')
    resultsf.write("r=" + str(r) + "\tresults=" + str(sumresults / nresults) + "\n")
    r += rstep
    
resultsf.close()
