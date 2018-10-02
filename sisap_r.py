#!/usr/bin/env python
#version 1.1

import sys,os,re,getopt
from subprocess import *
## Make unix pipe commands work w/o errors
import signal
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

index_name="sisap_r"
bprog = "build-mvp-vectors"
qprog = "query-mvp-vectors"
data_file = "/home/parnell/data/build_nasa.sisap.bin"
index_dir = "/home/parnell/data/indexes"
query_file = "/home/parnell/data/query_nasa.ascii"
output_dir = "%s_output" %index_name

results_file = "%s-results.txt" %index_name

PT_RESULT = re.compile("Total distances per query: ([^ ]+)$")

if not os.path.exists(output_dir):
	os.makedirs(output_dir)

r = rstart = 0.0
b = bstart = 3.0
rlimit = 1.0
rstep = 0.1

resultsf = open(results_file , "w") 
resultsf.write("\t# Calcs\n")

bckt_size = 3
### Build Index and write to file
cmd = [bprog,data_file,"0", index_name, str(bckt_size),"3","6"]
print ' '.join([c for c in cmd])
#p = Popen(cmd, stdout=PIPE)
#output = p.communicate()[0]
#buildf = open("%s/build.txt" %output_dir, "w")
#buildf.write(output)
#buildf.close()
cmdstr = ' '.join([c for c in cmd])
retcode = call(cmdstr, shell=True)
qfile = "%s/query.sisap" %output_dir

while r <= rlimit:
	print r
	result_file = "%s/query-%f" %(output_dir, r)
	qr = open(result_file, "w")
	qf = open(qfile, "w")
	line_count=0
	first = True
	### Queries need to be comma separated with radius as first value
	for line in open(query_file):
		line_count+=1
		if line_count > 10: break
		if first: 
			first = False
			continue
		line = line.replace(" ", ",")
		qf.write("%f,%s" %(r,line))
	qf.write("-0\n")
	qf.close()
	## Build indices

	cmd = [qprog,index_name]
	print cmd
#	p1 = Popen(["cat",qfile], stdout=PIPE)
#	p2 = Popen(cmd,stdin=p1.stdout,  stdout=PIPE)
#	output = p2.communicate()[0]
#	qr.write(output)
#	qr.close()
	cmdstr = "%s %s < %s 1<&-  2> %s " %(qprog,index_name,qfile , result_file)
	print cmdstr
	try:
#	    retcode = call(qprog +" "+ index_name + " < sisap_r_output/query.sisap 2> sisap_r_output/result.txt", shell=True)
	    retcode = call(cmdstr, shell=True)

	    if retcode < 0:
	        print >>sys.stderr, "Child was terminated by signal", -retcode
		sys.exit(1)
	    else:
	        print >>sys.stderr, "Child returned", retcode
	#	sys.exit(1)
	except OSError, e:
	    print >>sys.stderr, "Execution failed:", e

	for line in open(result_file, "a+"):
		m = PT_RESULT.match(line)
		if m :
			resultsf.write("r=" + str(r) + "\t" + m.group(1))

	r += rstep
	print r

