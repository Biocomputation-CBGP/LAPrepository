# LAP Repository
<img align="center" width="400" height="300" src="https://github.com/Biocomputation-CBGP/LAPrepository/blob/main/logo_LAP.svg">

LAP (https://www.laprepo.cbgp.upm.es/) is a repository dedicated to protocols meant to automate experimental workflows. Its entries have a structured format designed to expedite the creation of new protocols. It serves as a valuable resource for researchers and scientists aiming to enhance efficiency and reproducibility in their laboratory experiments.

In addition, LAP also contains scripts meant to help in the processing and analysis of the data created by the high-throughput experiments. These scripts are under the section LAPu and can be found on the same page.

All LAP and LAPu entries have instructions and example variable files attached to allow users to use them directly in their experiments.

## Structure of Github Repository

### LAPEntries Directory

1. LAP-Entry-1-Version-1 (Directory)
   1. code.py (Python script for LAP entry version 1)
   2. instructions.pdf (instructions to use and guidances to fill variable file of the protocol for version 1)
   3. example.xlsx (Example variable file to test the protocol 1 for version 1)
2. LAP-Entry-1-Version-2 (Directory)
   1. code.py (Python script for LAP entry version 2)
   2. instructions.pdf (instructions to use and guidances to fill variable file of the protocol for version 2)
   3. example.xlsx (Example variable file to test the protocol 1 for version 2)
3. LAP-Entry-2-Version-1 (Directory)
   1. code.py (Python script for LAP entry version 2)
   2. instructions.pdf (instructions to use and guidances to fill variable file of the protocol for version 1)
   3. example.xlsx (Example variable file to test the protocol 2 for version 1)
(Repeat this structure for other LAP entries and versions as needed)

### LAPuEntries Directory
1. LAPu-Entry-1-Version-1 (Directory)
   1. script.py (Directory)
   2. instructions.pdf (instructions to use)
   3. example (directory with example files)
2. LAPu-Entry-1-Version-2 (Directory)
   1. script.py (Directory)
   2. instructions.pdf (instructions to use)
   3. example (directory with example files)
3. LAPu-Entry-2-Version-1 (Directory)
   1. script.py (Directory)
   2. instructions.pdf (instructions to use)
   3. example (directory with example files)
(Repeat this structure for other LAPu entries as needed)


### SetFunctions Directory
1. function1.py (Function 1 used in LAPEntries, isolated for re-use)
2. function2.py (Function 2 used in LAPEntries, isolated for re-use)
3. function3.py (Function 3 used in LAPEntries, isolated for re-use)
4. function4.py (Function 4 used in LAPEntries, has dependencies on function2.py)
(Repeat this structure for other functions as needed)

 * README.md (Repository README containing an explanation of the objective of each function and its requirements)
