# LAPu-InsertsGenAnnotation-2.0.0

# Python program that aligns and annotate the reads that come from sanger or illumina sequencing to a reference genome with available annotations
# This program is designed to be run either in Linux or MacOS, it is not tested in Windows due to requirements like the installation of FastQC and BLASTn to be
# used in command line

# For that purpose this programs merge individual reads located in a directory (those can come from seuqencing for example),
# performs a BLAST (either with a fastq or fasta file),
# then with the start nucleotide of that BLAST output tracks which Locus tag or tags that allignments produces and merge the entry on the
# annotated genome with the entry of that BLAST allignment
# Other outputs and adjustments can be done by giving the program more arguments like trimming the sequences based on quality, other representations
# of the information cna be displayed, different columns can be provided in the final output and you can get more or less selective hits that come from the BLAST

# This prorgam has limitations like tracking the sequences to a map and some outputs are limited to 96-well plates sequenced plates and them having
# the structure of rows A-H and columns 1-12

# This script has been tested with bacterial genomes, specifically, for Pseudomonas Putida

# For more information about this script you can access to the LAP entry (...) or protocols.io entry (...)
# ----------------------------------------------------------------------------------------------------------------------------

# Import the neccesary python packages
import pandas as pd
import os
import subprocess
import argparse
import re
from Bio import SeqIO

description_message = """
\t\t--------------------------------------------------------------------------------------------------------------------------
\t\t--------------------------------------------------------------------------------------------------------------------------
\t\tProgram to align and annotate the reads that come from sanger sequencing to a reference genome with available annotations.
\t\tFor that purpose we need minimum:
\t\t - Reads to allign with the genome
\t\t - Genome sequence in fasta format
\t\t - Genome annotation in csv format\n
\t\tThe output of this program will be a directory which will contain max 4 files and 1 directory:
\t\t - Alignments file that will be the output as tsv (tab separated values) file of a BLASTn allignment
\t\t - SAM file that BLASTn gives as a possible output
\t\t - Table with the input reads match with the annotated genes, if possible 
\t\t - CSV file with a table with a 96-well plate layout and main Locus Tag hit for each position
\t\t - Directory with the sequences transformed in fastq files
\t\t--------------------------------------------------------------------------------------------------------------------------
\t\t--------------------------------------------------------------------------------------------------------------------------"""
epilog_message = """
\t\t--------------------------------------------------------------------------------------------------------------------------
\t\t--------------------------------------------------------------------------------------------------------------------------
\t\t                                    For more information visit
\t\t                            doi protocols io
\t\t                            enlace lapu
\t\t--------------------------------------------------------------------------------------------------------------------------
\t\t--------------------------------------------------------------------------------------------------------------------------"""

parser = argparse.ArgumentParser(description = description_message, epilog = epilog_message, formatter_class=argparse.RawTextHelpFormatter, usage = "%(prog)s [-h] [-q | -v] [-sm] [-out PATH_OUTPUT] [-f {table,all}] [-t THRESHOLD_RANGE] [-identity MAP_PLATE_IDENTITIES] [-cb FILE_NAMES_COLUMNS_BLAST] [-ca FILE_NAMES_COLUMNS_ANNOTATION] [-quality [QUALITY_FILE_EXTENSION] [-seq]] [-seq [TYPE_SEQENCING]] directoryReads extensionReads genomeSequence genomeAnnotation")

group = parser.add_mutually_exclusive_group()
# Positional arguments
parser.add_argument("directoryReads",
                    help = """
Files that will have the query strand(s) to search agains the genome sequence
                    """)
parser.add_argument("extensionReads", #former typeReads
                    help = """
Extension that the reads files will have, the vary for one sequence bussiness to others but all of them should be FASTA format type
In case the reads are not fasta extension, an additional directory will be provided with them in that format
Make sure that ONLY your reads have that extension in the given directory in the 'directoryReads' argument
                    """)
parser.add_argument("genomeSequence",
                    help = """
Genome fasta sequence that will the reads be compared to
                    """)
parser.add_argument("genomeAnnotation",
                    help = """
csv file that will have the genes of the genome annotated so insertions will be tracked to a gen
This file needs to have 3 column called 'Locus Tag', 'Start' and 'End' corresponding to the locus name, the start of that locus
and the end of that locus, respectively, so it can do the matching of reads and entries in the annotation file
They dont need to be in the selected columns of annotation but the need to be in the annotated file
                    """)
# Optional arguments
group.add_argument("-q","--quiet", action = "store_true",
                   help = """
Argument that settles if something should be displayed in the screen after running program.
If quiet is called nothing will be displayed
If neither quiet and verbose are called, minimal information will be displayed
This argument is not compatible with the verbose one
                   """)
group.add_argument("-v","--verbose", action = "store_true",
                   help = """
Argument that settles if something should be displayed in the screen after running program.
If verbose is called information will be displayed during the running of the program
If neither quiet and verbose are called, minimal information will be displayed
This argument is not compatible with the quiet one
                   """)
parser.add_argument("-out", default = "./results_script_blast", metavar = "PATH_OUTPUT",
                    help = """
Directory path where result files will be stored
By default will be stored at %(default)s
A message will be displayed if the %(default)s path is already created
                    """)
parser.add_argument("-f", "-filesOut", choices = ["table","all"], default = "all", dest = "filesOut",
                    help = """
Types of files that the program will give as an output:\n
 - table: csv file in which we will have the reads match with the annotated genes within other data of the BLAST allignment
 - all: (default value) both table and sam file will be th eoutput of the BLAST allignment
                    """)
parser.add_argument("-t","--thresholdRange", default = 0.01, type = float, metavar = "THRESHOLD_RANGE",
                    help = """
This range value is the proportion that the score can be lower than the best hit in the allignment that we allow as a "valid" allignment
This variable affects which reads, inc ase of having multiple allignments or not and the locus that we take as a hit
This variable is used when multiple allignments are obtained for 1 read input
By default is %(default) so allignments with the bit score lower than (1-thresholdRange)*Best hit score will be not considered
                    """)
parser.add_argument("-identity", metavar = "MAP_PLATE_IDENTITIES",
                    help = """
If the reads name has the name of the well between + and _ if it the files extension is seq or between 2 _ for any other extension; and you want the tracing between the identity of the sample
and the well in which the sequencing was you can provide an XLSX or CVS file in which the name of the sequenced sample is in the cell that corresponds to the well
it has been sequenced from (the identifier between + and _ or _ _).
Remeber to also put the name of the columns and the rows in the file
In case the identifiers are numbers, only 96-well plates sequenced plates are allowed counting from 1 to 96 top to bottom and left to right, i.e, the identifier 1 will be A1,
the identifier 2 will be B1 and the identifier 96 will be H12
                    """)
parser.add_argument("-cb","--columnsBLAST", metavar = "FILE_NAMES_COLUMNS_BLAST",
               help = """
If another set of columns are wanted from the BLAST alignment, all columns that are wanted need to be
named in a file in which the names of the columns are one per line.
For more references of the names of the columns needed, chech blast help
If nothing is provided, the columns will be the std + sstrand
This argument is developed with BLASTn 2.9.0+ and it can fail for other versions 
                    """)
parser.add_argument("-ca","--columnsAnnotation", metavar = "FILE_NAMES_COLUMNS_ANNOTATION",
                   help = """
If another set of columns from the annotation files are wanted a file should be provided with,
one per line, the names of the columns as stated in the annotation file of that genome.
The file needs to have a column called 'Start' and another 'End' that is the nucleotide of start and end
of the locus tag, respectivally.
By default, 8 columns from the annotation file will be provided:
\tLocus Tag, Feature Type, Start, End, Strand, Gene Name, Product Name and Subcellular Localization [Condifent Class]
                    """)
parser.add_argument("-quality", metavar = "QUALITY_FILE_EXTENSION", choices = ["ab1","fastq","qual"], nargs ='?', const = "abi",
                   help = """
Trimming of bad quality sequences or ends (3' nad 5') of those sequences.
Uses the sickle FASTQ trimming program that only admits Sanger, Solexa and Illumina sequencing.
These files will be searched in the same directory as the reads and they have to have the same name as the reads but with different extensions
This program is only design to trim single-end reads and only fastq, ab1 (abi in the choices) and qual.
When this argument is provided a file with all the read merged before and after the quality check and correspondent trimming will be created
and the sequence id of each read is going to be the name of the file without the extension.
                    """)
parser.add_argument("-seq", metavar = "TYPE_SEQENCING", choices = ["solexa","sanger","illumina"], nargs ='?', const = "sanger",
                   help = """
Type of sequencing which the single end reads have been obtained
This program only accepts illumina, sanger y solexa sequencing
By default the sequencing technique is set as sanger
                    """)
parser.add_argument("-sm","--summaryMap", action = "store_true",
                    help = """
A map displaying the main locus tag of the best hit identified by BLAST will be created. If a sequence has multiple hits, only the best hit will be shown.
Read/sequence names must follow specific formats based on the sequence type:
 - seq sequences: the well name or index should be between a plus sign (+) and an underscore (_). For example, read+A1_sequence or read+1_sequence indicates well A1.
 - other sequence: the well name should be between two underscores (_). For example, read_A1_sequence or read_1_sequence indicates well A1.
If numeric identifiers are used instead of well names, numbers 1 to 96 correspond to wells in a 96-well plate, ordered top to bottom and left to right
(e.g., 1 = A1, 2 = B1, 96 = H12). This expression will be looked for in the sequence ID of the read, not the file name. If the -quality argument is provided,
the sequence ID will match the file name.
This program supports reads from a 96-well plate, with columns numbered 1 to 12 and rows lettered A to H.
The final summary, including locus tag and well information, will be saved in the output directory specified by the -out argument.
                    """)

#  Variables that we need to have settled from the beginning
args = parser.parse_args()

# The quality argument and the seq one are one side by side, so if one is None it would come as an error
if args.quality and not args.seq:
    parser.error("The following arguments are required if you want to use the quality files of the sequences: seq")

directory_files = args.directoryReads
type_files = args.extensionReads
database = args.genomeSequence
file_annotation = args.genomeAnnotation
final_directory = args.out

# Let's check that the directory of reads exist, the genome sequence and the genome annotation file
# If something doesn't exist in the path given it will quit the program exactly
# This is done previously to anything to check if every essencial part is there

if not os.path.isdir(args.directoryReads):
    print(f"""------------------------------------------------------------------------------------------------------------------------------\n
 The directory {args.directoryReads} does not exist and it is neccessary for the program!
 Exiting program\n
------------------------------------------------------------------------------------------------------------------------------""")
    raise SystemExit(0)

if not os.path.isfile(args.genomeSequence):
    print(f"""------------------------------------------------------------------------------------------------------------------------------\n
 The file {args.genomeSequence} does not exist or it is not found and it is neccessary for the program!
 Exiting program\n
------------------------------------------------------------------------------------------------------------------------------""")
    raise SystemExit(0)

if not os.path.isfile(args.genomeAnnotation):
    print(f"""------------------------------------------------------------------------------------------------------------------------------\n
 The file {args.genomeAnnotation} does not exist or it is not found and it is neccessary for the program!
 Exiting program\n
------------------------------------------------------------------------------------------------------------------------------""")
    raise SystemExit(0)


#-----------------------------------
# General input data 
if args.verbose:
    message = f"""
------------------------------------------------------------------------------------------------------------------------------\n
    GENERAL INFORMATION RUNNING PROGRAM\n
        Reads file directory {args.directoryReads} with the {type_files} extension
        The genome sequence and gene annotation will be extracted from {args.genomeSequence} and {args.genomeAnnotation}
        The alignments final table will only consider hits that have {1-args.thresholdRange}*best hit score for each read
        Output files will be stored at {args.out}
        
------------------------------------------------------------------------------------------------------------------------------
    """
    print(message)


# Checking if the output directory is there so we do not overwrite a directory with the same name
# Output folder is name results_script_blast
if os.path.isdir(args.out):
    txt = input("------------------------------------------------------------------------------------------------------------------------------\n\n The directory '"+args.out+"' is going to be overwrited, are you sure? [y/n]:  ")
    if txt == "y":
        os.system("rm -r "+args.out)
        os.system("mkdir -p "+args.out)
        # print("------------------------------------------------------------------------------------------------------------------------------")
    elif txt == "n":
        print("""\n------------------------------------------------------------------------------------------------------------------------------
 
 Bye!

------------------------------------------------------------------------------------------------------------------------------""")
        quit() #We exit from the program in general
    else:
        print("""------------------------------------------------------------------------------------------------------------------------------
 Assumed NO, Exiting program
------------------------------------------------------------------------------------------------------------------------------""")
        quit() #We exit from the program in general
else:
    os.system("mkdir "+args.out) #Directory in which we are going to store the results


#-------------------------------------------
# In this section we are going to create the merged fasta file

# Lets set some variables that we need in case the quality is true
if args.quality == "qual":
    bioseq_file = "qual"
elif args.quality == "fastq":
    if args.seq == "solexa":
        bioseq_file = "fastq-solexa"
    elif args.seq == "sanger":
        bioseq_file = "fastq"
    elif args.seq == "illumina":
        bioseq_file = "fastq-illumina"
elif args.quality == "ab1":
    bioseq_file = "abi"

# Create the output file with the original fasta files
outfile = open(os.path.join(args.out,"all_reads_merged.fasta"), "w") # The directory where we will store the results

if args.quality: # Create the merged fastq file for its process in FastQC
    outfile_quality = open(os.path.join(args.out,"all_reads_merged_quality.fastq"), "w")
    if args.quality != "fastq": # If the quality is not fastq the fastq files will be created and could be used in posterior runs
        os.mkdir(os.path.join(args.out,"reads_fastq"))
    
for file in os.listdir(args.directoryReads): # We search throught the directory of reads
    file_name, file_extension = os.path.splitext(file)
    if file_extension[1:] == args.extensionReads: # We only take the files that are the reads becaus ethe directory could have more types of files
        with open(os.path.join(args.directoryReads,file), "r") as infile: # This is going to create a file with all the reads together
            outfile.write(infile.read().strip())
            outfile.write("\n")
            infile.close()
        
        if args.quality: # If we have the quality option as true
            # We read the file
            seq_quality = SeqIO.read(os.path.join(args.directoryReads, file_name+"."+args.quality), bioseq_file)
            # In case that the sequence id does not correspond to the file name, this will change it
            seq_quality.id = file_name
            # If it is not a fastq file, we will create one and store it in reads_fastq
            if args.quality != "fastq": # Esto ya estaba, simplemnet esto es que si no es fastqc simplemente se genera un fastqc en el que el id va a ser el nombre del archivo, no el ID que tiene en el read de secuenciacion
                SeqIO.write(seq_quality, os.path.join(args.out,"reads_fastq",file_name+".fastq"), "fastq")

            # We write the sequence in the merge file that will be use to analyze the quality
            SeqIO.write(seq_quality, outfile_quality, "fastq")

# Close files
outfile.close()
if args.quality:
    outfile_quality.close()


try: #We check if the database already exists, it works not only with the name of the db but also with the path to it
    subprocess.check_call(["blastdbcmd", "-info", "-db", database], stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    # check_call makes the expression in the list and checks if there is a exit code 0 (success) or other (error)
    # stdout and stderr are th eoutput and error message to a file that is temporal and not stored
    # If it is a success it means that the indexed genome works
    if args.verbose:
        print(f"""\n------------------------------------------------------------------------------------------------------------------------------\n
 Database {args.genomeSequence} already exists!
 Info of the DB:""")
        os.system("blastdbcmd -info -db "+database)
        print("""\n------------------------------------------------------------------------------------------------------------------------------""")
    elif not args.quiet and not args.verbose:
        print("""\n------------------------------------------------------------------------------------------------------------------------------
 
 Database already exists!
 Procceding to do BLAST
 
------------------------------------------------------------------------------------------------------------------------------\n""")
    # Gives the info for the database
except:
    if args.quiet:
    # Create the index so blastn can do the alignment
        os.system('makeblastdb -in '+database+' -dbtype nucl > /dev/null')
    # In case that check_all gives and error it creates the dabatase from the file given
    elif args.verbose:
        print(f"------------------------------------------------------------------------------------------------------------------------------\n\n Creating Database with the program 'makeblastdb' for {database}")
        os.system('makeblastdb -in '+database+' -dbtype nucl')
        print("""------------------------------------------------------------------------------------------------------------------------------\n""")
    elif not args.quiet and not args.verbose:
        print(f"""\n------------------------------------------------------------------------------------------------------------------------------
 
 Creating Database with the program 'makeblastdb' for {database}
 
------------------------------------------------------------------------------------------------------------------------------\n""")
        os.system('makeblastdb -in '+database+' -dbtype nucl > /dev/null')
        
#-------------------------------------------
#-------------------------------------------
# In the case that we want to perform a quality check we will perform the following lines
if args.quality:
    # We do the fastqc analysis that will generate the analysis in a zip file and also html files
    os.system(f"fastqc {os.path.join(args.out,'all_reads_merged_quality.fastq')}")
    
    # Now we ask the user what threshold wants
    print("------------------------------------------------------------------------------------------------------------------------------\nChech the FastQC file and decide the threshold for trimming!")
    threshold = input("Enter the Q value for trimming (by default 20): ")
    length_threshold = input("Enter the length (by default 20): ")
    
    if threshold == '':
        threshold = 20
    if length_threshold == '':
        length_threshold = 20
    
    # Now we trim with sickle
    if args.quiet:
        os.system(f"sickle se -f {os.path.join(args.out,'all_reads_merged_quality.fastq')} -t {args.seq} -o {os.path.join(args.out,'all_reads_merged_quality_trimmed.fastq')} -q {threshold} -l {length_threshold} --quiet")
    else:
        os.system(f"sickle se -f {os.path.join(args.out,'all_reads_merged_quality.fastq')} -t {args.seq} -o {os.path.join(args.out,'all_reads_merged_quality_trimmed.fastq')} -q {threshold} -l {length_threshold}")
    
    print("------------------------------------------------------------------------------------------------------------------------------\n")
    
    # Now we have to change that fastq trimmed to fasta reads so we can perform the allign
    with open(os.path.join(args.out,'all_reads_merged_trimmed.fasta'), 'w') as ofile:
        for record in SeqIO.parse(os.path.join(args.out,'all_reads_merged_quality_trimmed.fastq'), "fastq"):
            sequence = str(record.seq)
            ofile.write('>'+record.id+'\n'+sequence+'\n')

#-------------------------------------------
#-------------------------------------------
# Selected blastn output columns and genome annotations columns and significant score hit to elaborate final annotated table
# IMPORTANT PART OF THE SCRIPT, THIS CAN CHANGE FROM ONE VERSION OF BLAST TO ANOTHER ONE

possible_blast_columns = ["qseqid","qgi","qacc","qaccver","qlen","sseqid","sallseqid","sgi","sallgi","sacc","saccver","sallacc","slen","qstart","qend","sstart","send","qseq","sseq","evalue","bitscore","score","length","pident","nident","mismatch","positive","gapopen","gaps","ppos","frames",
                          "qframe","sframe","btop","staxid","ssciname","scomname","sblastname","sskingdom","staxids","sscinames","scomnames","sblastnames","sskingdoms","stitle","salltitles","sstrand","qcovs","qcovhsp","qcovus"]
table_ann = pd.read_csv(file_annotation)

# Before doing the check of the columns in the annotation lets check that the columns Locus Tag, End and Start are in the annotation file
if any(item_ann not in list(table_ann.columns) for item_ann in ["Start","End", "Locus Tag"]):
    print("""\n------------------------------------------------------------------------------------------------------------------------------
          \nThe annotation file needs to have the columns Locus Tag, End and Start to run the program\nExiting program\n""")
    raise SystemExit(0)

qacc, bitscore, sstart = [True, True, True]
if not args.columnsBLAST:
    columns_seq_alig = ["qaccver", "saccver", "pident", "length", "mismatch", "gapopen", "qstart", "qend", "sstart", "send", "evalue", "bitscore", "sstrand"]
        
else:
    # First we check that the file exists
    if not os.path.isfile(args.columnsBLAST):
        print(f"""------------------------------------------------------------------------------------------------------------------------------\n
 The file {args.columnsBLAST} does not exist or it is not found and it is neccessary for the custom BLAST columns output
 Exiting program\n
    ------------------------------------------------------------------------------------------------------------------------------""")
        raise SystemExit(0)
    
    # Import the file
    columns_raw = open(args.columnsBLAST).read().splitlines()

    # Check that all the elements of the columns given are allowed by BLAST
    if all(item in possible_blast_columns for item in columns_raw) == False:
        print("\nSome column or columns are not possible for this version of BLAST\n Exiting program\n")
        raise SystemExit(0)
    
    # Check if the query acc. y bit score columns is there because they are needed for the table cross
    columns_seq_alig = columns_raw
    
    if "qaccver" not in columns_raw:
        columns_seq_alig.append("qaccver")
        qacc = False
    
    if "bitscore" not in columns_raw:
        columns_seq_alig.append("bitscore")
        bitscore = False
    
    if "sstart" not in columns_raw:
        columns_seq_alig.append("sstart")
        sstart = False
    
# Now we create the header of the output of BLAST and the needed addition to the BLAST command
header_output_blast = "\t".join(columns_seq_alig)
    

#-------
locus_tag, start, end = [True, True, True]
if not args.columnsAnnotation:
    columns_ann = ["Locus Tag","Feature Type","Start","End","Strand","Gene Name","Product Name","Subcellular Localization [Confidence Class]"]
else:
    # First we check that the file exists
    if not os.path.isfile(args.columnsAnnotation):
        print(f"""------------------------------------------------------------------------------------------------------------------------------\n
 The file {args.columnsAnnotation} does not exist or it is not found and it is neccessary for the custom annotation .csv file columns in the final table
 Exiting program\n
    ------------------------------------------------------------------------------------------------------------------------------""")
        raise SystemExit(0)
    
    # Import the file
    columns_raw_ann = open(args.columnsAnnotation).read().splitlines()
    
    columns_ann = columns_raw_ann
    # Check that all columns of the annotation are in the file
    if all(item in table_ann.columns for item in columns_raw_ann) == False:
        print("\nSome column or columns are not in the annotation file of the genome\nExiting program\n")
        raise SystemExit(0)

    if "Locus Tag" not in columns_raw_ann:
        columns_ann.append("Locus Tag")
        locus_tag = False
    
    if "Start" not in columns_raw_ann:
        columns_ann.append("Start")
        start = False
    
    if "End" not in columns_raw_ann:
        columns_ann.append("End")
        end = False


range_value = args.thresholdRange # This is a variable we can set to identify significant alignments, score has been assesed according to our experimental results
# This range value is the proportion that the score can be lower than the best hit in the allignment that we allow as a "valid" allignment
# This variable affects which reads have multiple allignments or not and the locus that we take as a hit

    
# Perform BLASTn
if args.verbose:
    print(" BLAST command (s) that are going to be performed:")
    
if args.quality:
    reads_file = os.path.join(args.out,"all_reads_merged_trimmed.fasta")
else:
    reads_file = os.path.join(args.out,"all_reads_merged.fasta")
command_blastn_tabular_output = f"blastn -query {reads_file} -db {args.genomeSequence} -out {os.path.join(args.out, 'all_seq_aligned.tsv')} -outfmt '6 {' '.join(columns_seq_alig)}'"
if args.filesOut == "sam" or args.filesOut == "all":
    command_blastn_SAM_output = f"blastn -query {reads_file} -db {args.genomeSequence} -out {os.path.join(args.out, 'all_seq_aligned.sam')} -outfmt '17 {' '.join(columns_seq_alig)}'"
    os.system(command_blastn_SAM_output)
    if args.verbose:
        print(f"""\t- SAM output command
\t\t{command_blastn_SAM_output}""")
if args.verbose:
    print(f"""\t- Tabular output command
\t\t{command_blastn_tabular_output}
\n Final Headers that we are going to obtain in the tabular output:
\t{header_output_blast}\n""")
    
# It is possible to adjust with other arguments these expressions (check blastn manual)
# The way of changing the output is -outfmt "6 std" for the standard output, other example  -outfmt "6 std staxid" this will give us the standard output and the tax id of the subject
# It will give the output in the order of naming but without repetitions (if we put std score it will only print std)

if not args.verbose and not args.quiet:
    print(f" Making BLAST between {args.directoryReads} and {args.genomeSequence}\n")
os.system(command_blastn_tabular_output)
# os.system("rm all_reads_merged.fna") #We remove the file all_reads_merged but we can keep it deleting this command (or commenting)


# ----------------------------------
if not args.quiet and not args.verbose:
        print("""------------------------------------------------------------------------------------------------------------------------------

 Creating reads alignment - gene annotation Table
 
------------------------------------------------------------------------------------------------------------------------------\n""")
# Formatting of blastn output file 
command_add_header_txt = "echo '"+header_output_blast+"' | cat - "+final_directory+"/all_seq_aligned.tsv > temp && mv temp "+final_directory+"/all_seq_aligned.tsv"
os.system(command_add_header_txt)

# Add the header expression to the output of blastn

#state the files of blast, genome annotation file and the final table
file_magicblast = final_directory+"/all_seq_aligned.tsv"
final_table_name = final_directory+"/table_reads_genes_description.csv"

# Store the name of the summaryMpa in case that the user has asked for it
if args.summaryMap:
    file_map_summary_name = final_directory+"/summary_locus_grid_map.csv"

# Load tables as pandas dataframes
# table_ann has already been loaded
table_seq = pd.read_table(file_magicblast,sep="\t") 

# We create a column called key to be able to do a cross table (all possible combinations) with both tables
table_seq['key'] = 1
table_ann['key'] = 1

# Create a cross join table from sequences alignment and annotation to select rows with matches
table_cross = pd.merge(table_seq, table_ann, on ='key').drop("key", axis=1) # After doing this cross table we delete the column key

# Filter rows by only taking the rows that the subject (reference genome in this case) starting position is between the annotated genes
# this filtering is needed because there are lines in the table that the subject positions does not correspond to the annotated genes positions
table_matches = table_cross[(table_cross["sstart"] >= table_cross["Start"]) & (table_cross["End"] >= table_cross["sstart"])]

# Filter columns saving only the ones that have been selected previously in columns_seq_alig and columns_ann 
table_matches = table_matches[columns_seq_alig + columns_ann]


# Create a table with allignments that have not been matched with any annoted genes
table_not_matches = table_seq[~table_seq["qaccver"].isin(table_matches["qaccver"])][columns_seq_alig]

# Create the final table that is the alignments matched with genes with the ones not matched with any annotated gene
final_table = pd.concat([table_matches, table_not_matches], sort = False)

#------------------------------------------------------------

# We remove the allignments that are not within the threshold that we put so we discard these alignments according to the variable range_value
# We are adding a column with the score of the best hit of that read and then we delete the ones that are lower than score*threshold
final_table["Highest bit score"] = final_table.groupby('qaccver', sort=False)['bitscore'].transform('max')
final_table.drop(final_table[final_table["bitscore"] < final_table["Highest bit score"]*(1-range_value)].index, inplace=True)

# Now we can erase this column because it has already served its purpose
del final_table["Highest bit score"]

# We add the "warning" column in which we say if there are duplicates or not
final_table["Multiple Allignments"] = final_table.duplicated(subset = ["qaccver"], keep = False)

# Now we create the multiple locus column in case there are multiple allignments
locus_associated = [] 
for group_q_acc in final_table.groupby('qaccver', sort = False): # We group by query acc.
    locus_associated_query = list(final_table[final_table["qaccver"] == group_q_acc[0]]["Locus Tag"].values) #list of the locuses attached to the query read
    if len(locus_associated_query) > 1:
        locus_associated_query = locus_associated_query[1:]
    else:
        locus_associated_query = "-"
    locus_associated.append(locus_associated_query)

# Now we drop the duplicates only keeping the best alignment
# Warning: duplicates will also be dropped for alignments with the same score or within the threshold
final_table.drop_duplicates(subset ="qaccver", inplace=True, keep = "first")
# This is the moment in which we only keep the best hit for the allignment

# We add to the table the locus column
final_table["Rest of Locus Tag Associated"] = locus_associated

# Create the summary map dataframe to fill, we create it empty
if args.summaryMap:
    # Creamos el table entero sin nada dentro
    summary_map = pd.DataFrame(index = ["A", "B", "C", "D", "E", "F", "G", "H"], columns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])

# Let's add the columns of the identity if the argument is there
if args.identity != None:
    if not args.quiet and not args.verbose:
        print(" Adding Identity Columns to table")
    if args.verbose:
        print(f"""\n------------------------------------------------------------------------------------------------------------------------------
\n Adding Identity Columns to table with the information in {args.identity}""")
    # Let's check if the file exists and import it in case it does
    # We read in a different way the map in case it is a csv or an excel file
    _, extension = os.path.splitext(args.identity)
    if extension == ".csv":
            try:
                map_identities = pd.read_csv(args.identity, header = 0)
            except:
                raise Exception("File "+args.identity+" not found")
    elif extension == ".xlsx":
        try:
            map_identities = pd.read_excel(args.identity, engine = "openpyxl")
        except:
            raise Exception("File "+args.identity+" not found")
    else:
        raise Exception(f"-identity map file {args.identity} extension is {extension} and only csv and xlsx files are accepted for this argument") 

    
    # Prepare the column we are going to analyze and create the others that we are going to add
    position_plate_seq = []
    identity_sample = []
    list_queries = list(final_table["qaccver"])
    if args.summaryMap:
        list_locus = list(final_table["Locus Tag"]) #  We establish this valye in case summarymap is defined
    
    # Establish the regex expression we are going to search the plate sequencing well
    if args.extensionReads == "seq":
        regex_exp = r"\+([a-zA-Z]+)(\d+)_|\+(\d+)_"
    else:
        regex_exp = r"_([a-zA-Z]+)(\d+)(?=_)|_(\d+)(?=_)"
        
    # We create the identifiers between an index and the wells in case the position of the sequences are numbers
    rows = "ABCDEFGH"
    well_info = []
    for col in range (1,13):
        for row in rows:
            well_info.append((f"{row}{col}", row, col))
    dictionary_number_well = {i+1:well_info[i] for i in range(96)}

    # Run over the list of queries
    for query, locus in zip(list_queries, list_locus):
        everything_good = True
        matches = re.findall(regex_exp, query) # Vamos a coger todas los matches del patron
        if len(matches) == 0: # Aqui no tenemos un match en general, ni de numeros ni de letras mas numeros
            print(f"""
 WARNING: No matches for the regexs used for well was found in {query}
          For seq files the well name or number should be the last group of characters between a + and a _ (+A01_ or +2_ for example)
          For all other types of files, including txt, the well identity should be the last element surronded by _ (_A01_ or _2_ for example)
          You can have both well identifier or number in a sequence name but, in that case, the final match is going to be the ONLY one taken in account.
          For example, if you have both _A01_ and _13_ in a sequence and 13 is the last match, the identifier for this sequence is going to be 13, not A01
          Take in account that we are searching for one or more letters followed by a number or just a number between a plus and an underscore in seq files
          or between 2 underscores in other files extensions
                      """)
            position_plate_seq.append(float("nan"))
            everything_good = False
            
        else: # There is a match, maybe a ewll or maybe a number, but there is a match that will have 3 possible elements: well row, well column, number. There cant be a match that has all 3
            final_match = matches[-1]
            if final_match[0] and final_match[1]: # If it has the 2 first elements it is a well position
                position_plate_seq.append(final_match[0]+final_match[1])
                row_position = final_match[0]
                column_position = final_match[1]
            else: # If there is not the first and second element but the third, it is a number position
                if int(final_match[2]) < 1 and int(final_match[2]) > 96: # It cant fit in a 96-well plate
                    print(f" WARNING: We have found an identifier that corresponds to a number, {final_match[2]} but it is not between 1 and 96, which is incompatible with the current program that only can handle 96-well plates")
                    everything_good = False
                    position_plate_seq.append(float('nan'))
                else:
                    position_plate_seq.append(dictionary_number_well[int(final_match[2])][0])
                    row_position = dictionary_number_well[int(final_match[2])][1]
                    column_position = dictionary_number_well[int(final_match[2])][2]

        if everything_good: # If the identifier of this query is all good we add to the column the name of that cell
            try:
                identity_sample.append(map_identities[map_identities["Row/Column"]==row_position][str(int(column_position))].values[0])
            except:
                print(f" WARNING: The sequence well position {row_position+str(int(column_position))} was not found in {args.identity}")
                identity_sample.append(float('nan'))
            
            if args.summaryMap: # In case the summary map argument is given, the position in the final map will be filled with the locus
                if row_position not in summary_map.index or int(column_position) not in summary_map.columns:
                    print(f" The sequence well position {row_position+str(int(column_position))} cannot be placed in a table with 1-12 columns and A-H rows so it wont be included in the final summary map of locus-well")
                else:
                    summary_map.at[row_position, int(column_position)] = locus
        else:
            identity_sample.append(float('nan'))
    
    # Insert in the final table the new columns
    final_table.insert(1, "PositionSeqPlate", position_plate_seq)
    final_table.insert(2, "IdentitySample", identity_sample)

    # Export the final summary map
    if args.summaryMap:
        summary_map.to_csv(file_map_summary_name)

    if not args.quiet:
        print(" Volumes set in -identity are going to be introduced and, in case the argument -sm is set, the map is also created and filled")
        print("\n------------------------------------------------------------------------------------------------------------------------------\n")

elif args.summaryMap and args.identity == None: # We dont need or want the columns that track identity with a map
    # Get the queries
    list_queries = list(final_table["qaccver"])
    # Get the main hits
    list_locus = list(final_table["Locus Tag"])
    
    # Establish the regex expression we are going to search the plate sequencing well
    if args.extensionReads == "seq":
        regex_exp = r"\+([a-zA-Z]+)(\d+)_|\+(\d+)_"
    else:
        regex_exp = r"_([a-zA-Z]+)(\d+)(?=_)|_(\d+)(?=_)"
        
    # Create the identifiers index-well in case the position is a number and not a well
    rows = "ABCDEFGH"
    well_info = []
    for col in range (1,13):
        for row in rows:
            well_info.append((f"{row}{col}", row, col))
    dictionary_number_well = {i+1:well_info[i] for i in range(96)}

    # Run over the list of queries
    for query, locus in zip(list_queries, list_locus):
        everything_good = True
        matches = re.findall(regex_exp, query)

        if len(matches) == 0:
            print(f""" 
 WARNING: No matches for the regexs used for well was found in {query}
          For seq files the well name or number should be the last group of characters between a + and a _ (+A01_ or +2_ for example)
          For all other types of files, including txt, the well identity should be the last element surronded by _ (_A01_ or _2_ for example)
          You can have both well identifier or number in a sequence name but, in that case, the final match is going to be the ONLY one taken in account.
          For example, if you have both _A01_ and _13_ in a sequence and 13 is the last match, the identifier for this sequence is going to be 13, not A01
          Take in account that we are searching for one or more letters followed by a number or just a number between a plus and an underscore in seq files
          or between 2 underscores in other files extensions
                      """)
            continue
        else:
            final_match = matches[-1]
            if final_match[0] and final_match[1]:
                row_position = final_match[0]
                column_position = int(final_match[1])
            else:
                if int(final_match[2]) > 96:
                    print(f" WARNING: We have found an identifier that corresponds to a number, {final_match[2]} but it is superior than 96, which is incompatible with the current program that only can handle 96-well plates")
                    continue
                else:
                    row_position = dictionary_number_well[int(final_match[2])][1]
                    column_position = dictionary_number_well[int(final_match[2])][2]

            if row_position not in summary_map.index or column_position not in summary_map.columns:
                print(f" The sequence well position {row_position+str(int(column_position))} cannot be placed in a table with 1-12 columns and A-H rows so it wont be included in the final summary map of locus-well")
            else:
                summary_map.at[row_position, int(column_position)] = locus


    # Export the map
    summary_map.to_csv(file_map_summary_name)

    if not args.quiet:
        print(" The map of locus hit - map is created and filled")
        print("\n------------------------------------------------------------------------------------------------------------------------------\n")

#------------------
# Now we delete the columns that we havent put in the -cb or -ca arguments but were needed in the course of the script
if not qacc:
    del final_table["qaccver"]
if not bitscore:
    del final_table["bitscore"]
if not sstart:
    del final_table["sstart"]
if not locus_tag:
    del final_table["Locus Tag"]
if not start:
    del final_table["Start"]
if not end:
    del final_table["End"]

#------------------

#We export the table that we have created as final_table_name.csv
if args.filesOut == "table" or args.filesOut == "all":
    final_table.to_csv(final_table_name, index = False)

if args.verbose:
    number_reads_multialign = final_table["Multiple Allignments"].value_counts()[True]
    if args.identity and everything_good:
        mode_identity = True
    else:
        mode_identity = False
    print(f"""\tFINAL ALIGNMENT-ANNOTATION TABLE GENERAL INFORMATION\n
        \tDimension                                                                 {final_table.shape[1]} Columns and {final_table.shape[0]} Rows
        \tNumber of reads with multiallignments (within the threshold established)  {number_reads_multialign}
        \tPositionSeqPlate - Identity                                               {mode_identity}
\n------------------------------------------------------------------------------------------------------------------------------
    """)


#------------------
#Final encouraging message
if not args.quiet:
    print(" Program Done :)")
#------------------