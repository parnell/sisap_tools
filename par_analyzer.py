#!/usr/bin/env python3

###
# Author: Lee Parnell Thompson
# Vesion: 1.3.1
# analyze my results :)
# Disclaimer: I use these scripts for my own use, 
#   so caveat progtor, let the programmer beware
###

import sys,os,re,getopt, glob, math
from subprocess import *
from os.path import basename
## Make unix pipe commands work w/o errors
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)


def usage(out):
    print("Usage: ./par_analyzer.py [options] infile", file=out)
    print("  Valid Options are", file=out)
    print("     --results : use number of results", file=out)
    print("     --calcs : use number of distance calculations", file=out)
    print("     --time : [default] use time", file=out)
    print("     --max", file=out)
    print("     --mean: [default]", file=out)
    print("     --meanofmax", file=out)
    print("     --time", file=out)
    print("     --efficiency", file=out)
    print("     -v verbose", file=out)
    print("Example: ./par_analyzer.py  my_index", file=out)

try:
    opts, args = getopt.gnu_getopt(sys.argv[1:],
        "h?tvnam", 
        ("help","id=","seq=","show-lengths","results","tresults","max","avg","meanofmax",
        "time","efficiency","mean","total","calcs","avgperquery","count"))
except getopt.GetoptError as exc:
    print(exc.msg, file=stderr)
    usage(sys.stderr)
    sys.exit(2)

if (len(sys.argv) - len(opts) <= 1):
    usage(sys.stderr)
    sys.exit(2)

# Program Variable
rows = []
columns = []
M = {} ## values
MC = {}  ## our secondary M count
ntrees = []
metric = "mean"
datatype = 1 ## 0 for calcs,  1 for time, 2 for results
D = False
DLVL = 1 ## debugging level
result_type = "results"
# index_name = "par_sisap_r"
index_name = sys.argv[-1]
if index_name.endswith("_output"):
    index_name = index_name[:-7]
elif index_name.endswith("_output/"):
    index_name = index_name[:-8]

strdatatype = "time"
######### COMMAND LINE ARGUMENTS ##########
for o, a in opts:
    if o in ("-h", "--help","-?"):
        usage(sys.stdout)
        sys.exit()
    elif o == "-m": metric = "max"
    elif o == "--max": metric = "max"
    elif o == "-t": metric = "total"
    elif o == "--total": metric = "total"
    elif o == "-a": metric = "mean"
    elif o == "--avg": metric = "mean"
    elif o == "-v": D = True
    # elif o == "--tresults": datatype = 2
    elif o == "--meanofmax": metric = "meanofmax"
    elif o == "--efficiency": metric = "efficiency"
    elif o == "--mean": metric = "mean"
    elif o == "--totalperquery": metric = "totalperquery"    
    elif o == "--count": metric = "count"
    elif o == "--time":
        datatype = 1
        strdatatype = "time"
    elif o == "--calcs": 
        datatype = 0
        strdatatype = "calcs"
    elif o == "--results": 
        datatype = 2
        strdatatype = "results"


print ("metric=%s  type=%s" %(metric,strdatatype))

for line in open("%s_output/%s-column.txt" %(index_name,index_name)):
    vals = line.split('\t')
    vals = vals[1:]
    for c in vals : 
        c = c.strip()
        if c == "" : continue
        if (D) : print( "<%s>" %c)
        ntrees.append(int(float(c)))
        columns.append(str(int(float(c))))
    break

def initM(infile):
    global M,rows,MC
    first = True
    for line in open(infile):
        # if (D): print line
        if first:
            first = False
            pass
        else :
            vals = line.split("\t")
            rows.append(vals[0])
    # if (D) : print rows

    for r in rows:
        M[r] = {}
        MC[r] = {}
        for c in columns:
            M[r][c] = 0.0
            MC[r][c] = 0

def createResultFile(resultfile, queryfile, i, nt, radius):
    global D
    PT_AVG = re.compile("Average distances.*: *([^ ]+)$")
    PT_TOTAL = re.compile("Total distances.*: *([^ ]+)$")
    PT_RESULT = re.compile("([0-9]+).*objects found")
    PT_CALC = re.compile("([0-9]+).*calcs")
    PT_REAL = re.compile("real	0m(.*)s")
    resultsf = open(resultfile,"a")
    nresults = 0.0
    sumresults = 0.0
    
    for line in open(queryfile):
        if (D and DLVL > 10): print ("line=%s" %line)
        m = PT_CALC.match(line)
        if m : 
            resultsf.write("r=" + str(radius) + "\tcalc=" + m.group(1) + "\n")
        m = PT_RESULT.match(line)
        if m : 
            nresults += 1
            sumresults += int(m.group(1))
        m = PT_TOTAL.match(line)
        if m : 
            resultsf.write("r=" + str(radius) + "\ttotal_calcs=" + m.group(1))
        m = PT_AVG.match(line)
        if m : 
            resultsf.write("r=" + str(radius) + "\tavg_calcs=" + m.group(1))
        m = PT_REAL.match(line)
        if m : 
            resultsf.write("r=" + str(radius) + "\ttime=" + m.group(1) +"\n")
    if nresults == 0: 
        nresults = float('nan')
    resultsf.write("r=" + str(radius) + "\tresults=" + str(sumresults / nresults) + "\n")

    

## Main program
themax = 0
line_count = 0
first_tree = True
for nt in ntrees:
    if (D) : print ("!!!! number of trees=%d " %nt)
    sntrees = str(nt)

    maxes = {}
    maxk = 0
    # nt = number of trees
    localmax = 0.0
    for i in range(0,nt):
        localmax = 0.0
        indir = "%s_output/%d_%s/%d_%s_output"\
            %(index_name,nt,index_name,i,index_name)
        # print "FILE exists %s  == %d" %(indir,os.path.exists(indir))
        if not os.path.exists(indir):
            continue
        infile = "%s/%d_%s-%s.txt"\
            %(indir,i,index_name,result_type)
        if (os.path.exists(infile)):
            os.remove(infile) # we will be recreating this on the fly
        oldradius = None
        fval, rval, radius = None, None, None
        for f in glob.glob( os.path.join(indir, 'query-*') ):
            name, strradius = basename(f).split("-")
            createResultFile(infile,f,i,nt,float(strradius))

        if (D): print ("%d: %s" %(i,infile))
        if first_tree:
            initM(infile)
            first_tree = False

        # print columns
        # print rows
        first = True
        if not os.path.exists(infile):
            continue
        k = 0
        for line in open(infile):
            if not line: continue
            try:
                radius,result = line.split("\t")
                if oldradius != radius : 
                    oldradius = radius
                    k =0
#                    MC[radius][sntrees] = 0
                rtype,rval = result.split("=")
                fval = float(rval)
                if ( (datatype == 0 and (rtype != "total_calcs" and rtype != "calc")) or (datatype ==1 and rtype != "time") or (datatype ==2 and rtype != "results")): 
                    continue
                k +=1
                if (D): print ("%d: '%s'   rtype=%s  rval=%s" %(i,line.strip(),str(rtype),str(rval)), end="")
                if (math.isnan(fval)):
                    print ("failed at ", line)
                    continue
            except:
                print ("failed at ", line)
                continue
            MC[radius][sntrees] += 1
            localmax
            # print radius.strip(), result.strip(), rtype, rval
            if metric == "total":           M[radius][sntrees] += fval
            elif metric == "efficiency":    M[radius][sntrees] += fval
            elif metric == "mean":          M[radius][sntrees] += fval
            elif metric == "totalperquery": M[radius][sntrees] += fval
            elif metric == "max":           M[radius][sntrees] = max(fval,M[radius][sntrees])
            elif metric == "meanofmax": localmax = max(localmax,fval)
        # print "%d local max = %f    %f   %f" %(i, localmax, M[radius][sntrees], MC[radius][sntrees])
        if metric == "meanofmax":     M[radius][sntrees] += localmax
    if not MC[radius][sntrees]:
        continue
    if (D): print ("%d : nrecords=%d" %(i,MC[radius][sntrees]))
    if metric == "meanofmax":
        ## for each radius, take the sum of the maximum value
        for r in M.keys():
            print ("blah %f  %d" %(M[r][sntrees] , nt))
            M[r][sntrees] = M[r][sntrees] / nt
    if metric == "efficiency":
        for r in maxes.keys():
            tot = 0.0
            dev = 0.0
            themax = 0.0
            for k in maxes[r].keys():
                tot += maxes[r][k]
                # print tot
                themax = max(maxes[r][k],themax)
            mean = (tot / len(maxes[r]))
            M[r][sntrees] = mean / themax
            # mean = tot / len(maxes)
            # print "mean=%f   themax=%f" %(mean,themax)
            M[r][sntrees] = mean/themax
            for k in maxes[r].keys():
                dev += (maxes[r][k]-mean)**2
            M[r][sntrees] = math.sqrt(dev)
    if metric == "mean":
        ## for each radius
        for r in M.keys():
            M[r][sntrees] = M[r][sntrees] / MC[r][sntrees]
    if metric == "count":
        ## for each radius
        for r in M.keys():
            M[r][sntrees] = MC[r][sntrees]
    if metric == "totalperquery":
        for r in M.keys():
            tot = 0.0
            count = 0
            for k in M[r].keys():
                tot += M[r][k]
                count +=1
            # print "%s %s %d %d " %(r, sntrees,tot,count)
            # print "%d %d " %(tot,MC[r][sntrees])
            M[r][sntrees] = tot / MC[r][sntrees]
# print M
print
def comp(x,y):
    # print "!!!!!x=%s" %x
    # print "!!!!!y=%s" %y
    # print x.split("=")
    # print len(x.split("="))
    if len(x.split("=")) > 1:
        x = float(x.split("=")[1])
        y = float(y.split("=")[1])
    else:
        # print x
        # print len(x.split())
        x = float(x)
        y = float(y)
        
    if x < y : return -1
    elif x > y : return 1
    else: return 0
            
            
for r in M.keys():
    for c in sorted(M[r].keys(),comp):
        print ("\t" + c, end="")
    print()
    break

for r in sorted(M.keys(),comp):
    print (r, end="")
    for c in sorted( M[r].keys(),comp):
        print ("\t" + str(M[r][c]), end="")
    print()
