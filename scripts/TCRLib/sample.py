#! /bin/env python

def main(): pass

class Sample(object):

    def __init__(self, TCRcaller, sampleName=None,sampleId=None,refType=None):
	self.name = sampleName
	self.id = int(sampleId)
	self.refType = refType
	self.path = TCRcaller.path+'/samples/'+self.name
	self.scriptPath = TCRcaller.path+'/samples/'+self.name+'/script'
	self.dataPath   = TCRcaller.path+'/samples/'+self.name+'/data'
	self.logPath    = TCRcaller.path+'/samples/'+self.name+'/logs'
	self.fastqcPath = TCRcaller.path+'/samples/'+self.name+'/fastQC'
	self.dependencies = {}

    @property
    def readCount(self, ):
	tmpCounter = 0
	for filePairId,readCount,fastq1,fastq2,sampleId in AnalysisPipe.database.getFastqs():
	    if int(sampleId) == self.id:
		try: tmpCounter+= readCount
		except TypeError: return 'Unknown'
	return tmpCounter

    def getFastqs(self,):
	self.fastqIds = []
	for filePairId,readCount,fastq1,fastq2,sampleId in AnalysisPipe.database.getFastqs():
	    if int(sampleId) == self.id:
		self.fastqIds.append(filePairId)
		yield [filePairId,readCount,fastq1,fastq2,sampleId]

    def createDirs(self):
        import os
        try: os.makedirs(self.path)
        except OSError:pass
        try: os.makedirs(self.scriptPath)
        except OSError:pass
        try: os.makedirs(self.dataPath)
        except OSError:pass
        try: os.makedirs(self.fastqcPath)
        except OSError:pass
        try: os.makedirs(self.logPath)
        except OSError:pass

    def updateOrgReadCounts(self,):
	AnalysisPipe.database.updateFastqReadCount(self)

    def getReadOrientationStats(self,):

	import time
	import operator
	import shutil
	import os
	import sys
	import pysam
	import time
	orientations = {'PP':0,'FR':0,'FRsp':0,'FF':0,'RF':0,'RR':0,'difChrom':0}
	
	try: uppmax_temp = os.environ["SNIC_TMP"]
	except:
	    uppmax_temp = None
	    print 'Not on uppmax no temporary directory'
    
	if not os.path.exists(self.dataPath+'/'+self.name+'.noDuplicates.bam'): AnalysisPipe.logfile.write('#WARNING#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Skipping oriantations stats for sample '+self.name+' the infile has not been created yet...\n'); return orientations
    
	if uppmax_temp:
	    try:os.mkdir(uppmax_temp+'/fnuttglugg_TMP')
	    except OSError:pass
	    if not os.path.exists(uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bam'):
		AnalysisPipe.logfile.write('#LOGMSG#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Copying '+self.dataPath+'/'+self.name+'.noDuplicates.bam'+' to temp location for faster reading from disk, '+uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bam'+' \n')
		shutil.copy(self.dataPath+'/'+self.name+'.noDuplicates.bam',uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bam')
	    else:
		print 'WARNING: rerun of '+uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bam'+' skipping copy!!'
		AnalysisPipe.logfile.write('#WARNING#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# WARNING: rerun of '+uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bam'+' skipping copy!!\n')
	    bamfileName  = uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bam'
	else:bamfileName = self.dataPath+'/'+self.name+'.noDuplicates.bam'
	if uppmax_temp:
	    try:os.mkdir(uppmax_temp+'/fnuttglugg_TMP')
	    except OSError:pass
	    if not os.path.exists(uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bai'):
		AnalysisPipe.logfile.write('#LOGMSG#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Copying '+self.dataPath+'/'+self.name+'.noDuplicates.bai'+' to temp location for faster reading from disk, '+uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bai'+' \n')
		try: shutil.copy(self.dataPath+'/'+self.name+'.noDuplicates.bai',uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bai')
		except IOError as e: pass
	    else:
		print 'WARNING: rerun of '+uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bai'+' skipping copy!!'
		AnalysisPipe.logfile.write('#WARNING#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# WARNING: rerun of '+uppmax_temp+'/fnuttglugg_TMP'+'/'+self.name+'.noDuplicates.bai'+' skipping copy!!\n')
	
#	bamfileName = 	self.dataPath+'/'+self.name+'.noDuplicates.bam'
	try: bamfile = pysam.Samfile(bamfileName, "rb")
	except IOError:
	    AnalysisPipe.logfile.write('#WARNING#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Skipping oriantation stats for sample '+self.name+' the infile has not been created yet...\n')
	    return orientations
	except ValueError:
	    AnalysisPipe.logfile.write('#WARNING#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Skipping oriantation stats for sample '+self.name+' the infile is not finished for processing...\n')
	    return orientations
    
	AnalysisPipe.logfile.write('#LOGMSG#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Loading oriantation stats for sample '+self.name+'...\n')
	try:
	    for read in bamfile.fetch():

		orientation = None
		if read.is_paired and not read.is_unmapped and not read.mate_is_unmapped:
		    if read.tid == read.rnext:
			if read.is_proper_pair:
			    orientation = 'PP'
			elif   read.pos < read.pnext:
			    if read.is_reverse: orientation = 'R'
			    else: orientation = 'F'
			    if read.mate_is_reverse: orientation += 'R'
			    else: orientation += 'F'
			elif read.pnext < read.pos:
			    if read.mate_is_reverse: orientation = 'R'
			    else: orientation = 'F'
			    if read.is_reverse: orientation += 'R'
			    else: orientation += 'F'
			elif   read.pos == read.pnext: orientation = 'FRsp'
		    else: orientation = 'difChrom'
		    orientations[orientation]+=1
	    total = sum(orientations.values())

	    output = self.name+'\n'
	    for thingy,plingy in orientations.iteritems():
		output+= thingy+' '+str(percentage(plingy,total))+'\n'
	    print output

	except ValueError as e:
	    if e == 'fetch called on bamfile without index':
		AnalysisPipe.logfile.write('#WARNING#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Skipping insert size plot for sample '+self.name+' the bam index is not present...\n')
		sys.stderr.write('#WARNING#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Skipping insert size plot for sample '+self.name+' the bam index is not present...\n')
		return orientations
	AnalysisPipe.logfile.write('#LOGMSG#'+time.strftime("%Y-%m-%d:%H:%M:%S",time.localtime())+'# Loaded oriantation stats for sample '+self.name+' joining to main...\n')
	return orientations

    def align(self,):
	#bowtie2 -x references/ncbi.T_cell_receptor_beta.Human.mRNA.fa -U data/mnt/davidson/sandberglab/pipeline2.0/rnaseq/hsa/simone_picelli_T-cells/rawdata/$i/Run00221_L7_1_140213_SN893_0221_BC3H8JACXX_*.fastq.gz -U data/mnt/davidson/sandberglab/pipeline2.0/rnaseq/hsa/simone_picelli_T-cells/rawdata/$i/Run00223_L3_1_140220_SN893_0223_BC3JDHACXX_*.fastq.gz -S $i.sam --very-sensitive-local -p16
	#samtools view -Sb $i.sam > $i.bam
	#samtools sort $i.bam $i.sorted
        #samtools index $i.sorted.bam
	pass
    
    def getAlignedReadsPairs(self, ):
	#samtools view -F 4 -q 20 $i.sorted.bam | cut -f 1,10,11 | awk '{print "@" $1 "\n" $2 "\n+\n" $3}' > $i.mapqMoreThan20.fq
	pass

    def assemble(self,):
#	velveth $i 21 -fastq -short $i.mapqMoreThan20.fq
#	velvetg $i/ -cov_cutoff auto
	pass

    def report(self,):
#	cat $i/contigs.fa
#	mv -v $i* $i
#	echo -e "\n### The reads mapped to the following gi: "
#	samtools view -F 4 -q 20 $i/$i.sorted.bam | cut -f3 | sort | uniq -c;
#	echo -e "\n### same as to the following sequences: "
#	echo -e $(for name in $(samtools view -F 4 -q 20 $i/$i.sorted.bam | cut -f3 | sort | uniq); do grep $name references/ncbi.T_cell_receptor_beta.Human.mRNA.fa;done) | sed s/\>/\\\n/g | grep -P "T|cell|receptor|beta|$" --color=Always
	pass
    

if __name__ == "__main__": main()