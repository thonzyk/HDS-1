# HDS-1
semester project: phonetic transcription of written czech text

## Install
### Mandatory 
* python 3.7+
* packages:
  * re
  * pathlib
  * numpy

### Optional (for metrics)
* packages:
  * time
  * unittest
  * sklearn
  * termcolor
    
## Run
Run the **__main__.py** script to run the algorithm on the **vety_HDS.ortho.txt** file.<br/>
The results are saved in the **src/data/output/vety_HDS.phntrn.txt** file after the algorithm is finished. 

For advanced metrics run the tests in **src/tst/test_performance.py**