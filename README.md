Phornthep Sachdev
5680836

Data Communication Networks Project 1 - Resumable Concurrent Download File

python libraries utilized :
	sys , pickle, os, asyncore, urlparse, socket

Downloading Using One Connection:
1. Supports Downloading/Resuming
2. Checks the current directory for filenames and prompts to overwrite accordingly
3. Methodology: Use pickle to store header location
4. Error Handling to an extent

While downloading using 1 connection, there will be a pickle file with the prefix of the filename being downloaded followed by '.pickle'. This file holds vital information about the partially downloaded file, wont be able to resume without it.

Downloading Using More than one Connection:
1. Utilized asyncore
2. Split the file into different partitions according to the size. All the connections specified will work on each partition before moving on to another partition.

Download using more than one connection also uses pickles.

-------------------------------------------

Features Supported:
1. Can increase and decrease the number of connections use.
2. HTTP status code handling
3. URL Redirection

Not Supported:
1. If downloaded using many connections, have to use -c to continue downloading. Cannot switch to normal non-concurrent download.
2. Chunked Transfer Encoding
3. Scenario when no Content Length available
	
-------------------------------------------

- Usage: ./srget.py -o [output file] [url]
- Usage: ./srget.py -o -c [numConn] [output file] [url]

Thank you for reading this.
Starting early for the next one :)
