# VMWare interview questions
Interview questions to Log Insight team DevOps


####Task 1.
Language: python

Application type: command line

Arguments: path to a text file.

Text file content: multiline, each line containing the following info:
 ```
<ip address>, <username>/<password>     # active line
;<ip address>, <username>/<password>  # commented line & must be ignored
```
App logic: process the input file, grab active lines, ssh to each destination, 
grab current cpu/memory and disk utilization, print to console.



####Task 2.
Implemented in `src/sort_random_matrix.py`

Language: python

Application type: command line

Prerequisite: do not use any libraries or available algorithms when solving this problem. 

Try to stick to language basics such as looks, arrays, dicts, ets.
Arguments: none

App logic: pick a random number greater than 10 and less than 20 and randomly initialize a 2D array with 1s and 0s. 

Print the matrix. Implement an algorithm of sorting 1s to the right and 0s to the left.
An example on a smaller matrix that follows:

Initial matrix
```
1001
0010
1101
0110
```
Final sorted matrix:
```
0011
0001
0111
0011
```