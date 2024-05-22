# Input
This script needs a serious files as an input, minimum 2 files and 1 directory and maximum 3 files and 1 directory.

In addition, this program needs another argument that will be the **extension** of the files in _sequencing_results_ that the sequences have, in this case, that extension is txt

### sequencing_results

Folder that contains 4 types of files:

* _.ab1_: File that correspond to the DNA electropherogram results of the corresponding sequence file
* _.phd.1_: Phred file that conatins the quality values for each of the nucleotides sequenced in the respective sequence file
* _.pdf_: visual form of the results in the phd.1 file
* _.txt_: File that contains the sequenced sequence in fasta format

Each sequence have the 4 files associated but only the ab1 and txt files are going to be used, the first one to perform a quality analysis, if requested in the command line with arguments like **-quality** and the txt file that will be used to perform th eallignment against the genome holded in the file _Pseudomonas_putida_KT2440_110.fna_

### Pseudomonas_putida_KT2440_110.fna

Genome sequence of Pseudomonas putida KT2440 in FASTA format.

This file will be used to do the sequence allignment between each one of the sequence file in _sequencing_result_ with BLASTn.

With the output of this allignemnt is how the final table will be constructed between the start position of the allignment and the _Start_ and _End_ column of the file _Pseudomonas_putida_KT2440_110.csv_

### Pseudomonas_putida_KT2440_110.csv

Table that contains annotation data about the genome of _Pseudomonas putida KT2440_ such as the gene name that corresponds to a locus.

Some columns of this table will be displayed in the final table, but they are customizable, the only requirements is the _Start_, _End_ and _Locus Tag_ columns that indicates in which nucleotide of the genome this locus starts and ends, and the how the locus is named, respectivelly.

By default the columns that are going to be returned are _Locus Tag_, _Feature Type_, _Start_, _End_, _Strand_, _Gene Name_, _Product Name_, _Subcellular Localization [Confidence Class]_, so all of these columns should be present in this file in case no columns are provided. To know more about the customization of the final columns check the argument **-ca** of the program with the help argument of the script, **-h**

### map_identity_plate.xlsx (optional)

Table with the same dimensions as the labware had in the sequencing, in other words, the same columns and rows as the labware with their respective names.

This document will be used to track the names of the samples with their respective allignments and annotation in the final table.

This tracking will only work if in the names of the files in the directory with the sequences they have this location in their names, enclosed by underscores.

For example, if the name of the file is _22CCRAA000_A01_premix.txt_ this file will be tracked with the well A1 or cell in the table corresponding to the column with the name 1 and row with the value A. If the name file does not contain that A01 between underscores, this tracking will not be possible to do and providing this file will cause an error will be raised
