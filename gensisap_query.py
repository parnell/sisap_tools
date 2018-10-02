#!/usr/bin/env python

infile = sys.argv[-2]
outfile = sys.argv[-1]

qf = open(outfile, "w")
line_count=0
limit = None
### Queries need to be comma separated with radius as first value
for line in open(query_file):
	line_count+=1
	if limit and line_count > limit: break
	if line_count == 1: continue
	line = line.replace(" ", ",")
	qf.write("%f,%s" %(r,line))
qf.write("-0\n")
qf.close()
