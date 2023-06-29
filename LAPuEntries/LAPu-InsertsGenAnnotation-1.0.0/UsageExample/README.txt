Input:
- sequencing_results
- Pseudomonas_putida_KT2440_110.fna
- Pseudomonas_putida_KT2440_110.csv
- map_identity_plate.csv

Command Performed in command line:
'''
python3 alignment_script.py sequencing_results txt Pseudomonas_putida_KT2440_110.fna Pseudomonas_putida_KT2440_110.csv -out results_annotation -quality ab1 -seq sanger -identity map_identity_plate.csv
'''

Output:
- reads_fastq
- all_reads_merged.fasta
- all_reads_merged_quality.fastq
- all_reads_merged_quality_fastqc.html
- all_reads_merged_quality_fastqc.zip
- all_reads_merged_quality_trimmed.fastq
- all_reads_merged_trimmed.fasta
- all_seq_aligned.sam
- all_seq_aligned.tsv
- table_reads_genes_description.csv
