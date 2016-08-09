import os
import logging
import uuid

from Bio import AlignIO
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.Emboss.Applications import NeedleCommandline

def alignmentFilter(seqs, template, gapopen=10, gapextend=0.5, lo_cutoff=300, hi_cutoff=1000,
                    cleanup=True):
    logging.info('Started alignment-based filtering')
    start_nSeqs = len(seqs)
    
    # Save the template and sequences as temporary fasta files
    # Probably some hacking that can be done in the NeedleCommandline stuff
    # But for now, this is easiest.
    
    template_fname = 'temptemplate.fa'
    seqs_fname = 'tempseq.fa'
    
    with open(seqs_fname, 'w') as sh:
        SeqIO.write(seqs, sh, 'fastq')
    
    with open(template_fname, 'w') as tem:
        tempSeq = SeqRecord(Seq(template), id='template', name='template')
        SeqIO.write(tempSeq, tem, 'fasta')
        
    # Generate alignment command, run the alignment
    logging.info('Began EMBOSS needle routine with settings:\ngapopen: %i\ngapextend: %i\nlo_cutoff: %i\nhi_cutoff: %i' % (gapopen, gapextend, lo_cutoff, hi_cutoff))
    ofilen = 'temp_'+str(uuid.uuid4())+'.needle'
    needle_cline = NeedleCommandline(asequence=template_fname, bsequence=seqs_fname, gapopen=gapopen,
        gapextend=gapextend, outfile=ofilen)
    needle_cline()
    logging.info('Finished EMBOSS needle routine')
    
    # Read in alignment file
    # **NOTE: This code assumes you've edited EmbossIO to keep track of the score
    # and keep it as an annotation of the MultipleSeqAlign object
    
    alnData = AlignIO.parse(open(ofilen), "emboss")
    newSeqs = cull_alignments(alnData, lo_cutoff=lo_cutoff, hi_cutoff=hi_cutoff)
        
    # Exit routine
    if cleanup:
        logging.info('Cleaning up temp files')
        os.remove(template_fname)
        os.remove(seqs_fname)
        os.remove(ofilen)
    logging.info('Finished alignment-based filtering. Kept %i of %i sequences.' % (len(newSeqs), start_nSeqs))
    return newSeqs


def cull_alignments(alnData, lo_cutoff=400, hi_cutoff=650):
    newSeqs = []

    for alignment in alnData:
        if (alignment.annotations['score'] > lo_cutoff) and (alignment.annotations['score'] < hi_cutoff): # Score cutoff
            if not (str(alignment[0].seq).count('-') > 0): # Template should have no gaps, and should contain the whole non-template sequence
                newSeqs.append(alignment[1])
                newSeqs[-1].annotations['alnscore'] = alignment.annotations['score']
                # Shouldn't need indexing annotation...
    
    return newSeqs
