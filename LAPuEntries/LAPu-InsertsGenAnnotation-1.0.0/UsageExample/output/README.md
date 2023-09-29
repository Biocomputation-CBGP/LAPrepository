# Output
Due to the argument we have given in the command (**-quality ab1 -seq sanger -identity map_identity_plate.csv**) we will have 10 outputs

The outputs have been given by saying that the trimming value (Q) and the length as **20** after checking the file _all_reads_merged_quality_fastqc.html_, an input required by the script because we have set the argument **-quality**. The output that is given because of this command will be stated as _optional_

All of these outputs are in a folder called _results_annotation_ because we have stated that in the command (**-out results_annotation**), otherwise, they would have been in a folder called __

### reads_fastq (optional)

Directory with the reads stated in the input _sequencing_results_ transformed to fastq to perform the trimming of the sequences.

This folder could be used as an input of this script

### all_reads_merged.fasta (optional)

Merged of all the sequences in the directory _sequence_results_ in FASTA format

### all_reads_merged_quality.fastq (optional)

Merged of all the sequences in the directory _reads_fastq_. This file will be used to analyze the quality of the sequences to set a Q and length to trim

### all_reads_merged_quality_fastqc.html (optional)

HTML page created by the FastQC ubuntu program in which there is an analysis of the quality of the reads given in _all_reads_merged_quality.fastq_

This is the file that should be looked to establish the Q and length that is going to be asked as an input by the program

### all_reads_merged_quality_fastqc.zip (optional)

ZIP file that will be the output of the FastQC ubuntu program in which there is an analysis of the quality of the reads given in _all_reads_merged_quality.fastq_

This file contains the HTML report as well as some summary of it and the graphics associated to it

### all_reads_merged_quality_trimmed.fastq (optional)

Sequences in _all_reads_merged_quality.fastq_ after trimming them with the values given by the user (Q and length) and the ubuntu package **sickle**

### all_reads_merged_trimmed.fasta (optional)

Sequences without quality from the file _all_reads_merged_quality_trimmed.fastq_ to perform the allignment against the genome in the input file _Pseudomonas_putida_KT4220_110.fna_

### all_seq_aligned.sam



### all_seq_aligned.tsv



### table_reads_genes_description.csv
