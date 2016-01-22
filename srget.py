import socket as sk 
import os
from urlparse import urlparse

def mkDownloadRequest(serv, objName):
	return ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n\r\n").format(o=objName, s=serv)

def mkHeadRequest(serv,objName):
	return ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=objName, s=serv)

def mkResumableRequest(serv,objName,file):
	S = os.stat(file)
	size = S.st_size
	return ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-"+"\r\n\r\n").format(o=objName,s=serv,h=str(size))

def storeURL(url,filename):
	f = open("URL"+filename,"w")
	f.write(url)
	f.close()

def writeHeader(serv,objName,header_file,port,timeout):
	Head = open(header_file,"w+") # w+ both read and write
	sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
	sock.settimeout(timeout)
	try:
		sock.connect((serv,port))
		requestHead = mkHeadRequest(serv,objName)
		sock.send(requestHead)
		data = ""
		while True:
			data += sock.recv(1024)
			#print data[len(data)-4:len(data)] == "\r\n\r\n"
			if data[len(data)-4:len(data)] == "\r\n\r\n" or len(data)==0:
				sock.close()
				Head.write(data)
				break
	except sk.gaierror, e:
		print "Invalid URL name"
	except sk.error, ex:
		print "Caught exception socket.error : %s" % ex
	Head.close()

def writeFile(serv,objName,file,port,header_file,timeout):
	size_header = os.stat(header_file).st_size
	content_len = getHeader(header_file)[1]["Content-Length"]
	print size_header , content_len
	f = open(file,"w+") # w+ both read and write
	sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
	sock.settimeout(timeout)
	try:
		sock.connect((serv,port))
		requestFile = mkDownloadRequest(serv,objName)
		sock.send(requestFile)
		length = 0
		while True:
			data = sock.recv(1024)
			length += len(data)
			if (length-size_header)==int(content_len) or (length-size_header)==content_len:
				sock.close()
				break
			f.write(data)
	except sk.gaierror, e:
		print "Error Connecting to Server"
	except sk.error, ex:
		print "Caught exception socket.error : %s" % ex
	f.close()

def NoHeaderFile(file,header_file): #split the main file from the header 
	f = open(file,"r")
	lines = f.readlines()
	f.close()
	f = open(file,"w")
	header_count = getHeader(header_file)[0]
	#print header_count
	count = 0
	for line in lines:
		if count < header_count:
			count += 1
		else:
			f.write(line)
	f.close()

def getHeader(filename): #Get the header dictionary	#returns tuple (line_count, dict)
	f_open = open(filename,"r")
	dct = dict()
	count = 0
	for line in f_open.readlines():
		if count == 0:
			count += 1
			continue
		elif line != "\r\n":
			separate = line.split(":",1)
			dct[separate[0]] = separate[1][1:len(separate[1])-2]
		count += 1
	f_open.close()
	return count, dct

def isDL_complete(header_File,file): #check if download is complete
	C_len = getHeader(header_File)[0]
	info = os.stat(file)
	return info.st_size == int(C_len)

def main(filename,url):
	temp_filename = "DL" + filename
	parsed = urlparse(url)
	Host_serv = parsed.netloc
	Host_path = parsed.path
	Host_port = parsed.port
	if Host_port == None:
		Host_port = 80
	toOverwrite = ""
	if os.path.exists("DL"+filename): #if the partially downloaded file exists
		f = open("URL"+filename,"r")
		if url==f.readlines()[0]:#check if the same URL
			print "Check if file modified using E-tags or Last Modified"
			print "If True: re download the file"
			print "Else:  Resume Download"
	elif os.path.exists(filename):
		print "File exists: Do you want to overwrite the file?"
		while toOverwrite != "Y":
			toOverwrite = raw_input("Do you want to overwrite the file? (Y/N)") 
			if toOverwrite.upper() == "N":
				print "Please Enter New Filename"
				return
		print "Overwriting the original file"
	else:
		print "Download File"

website = "http://cs.muic.mahidol.ac.th/~ktangwon/bigfile.xyz"
servName ="cs.muic.mahidol.ac.th"
objName = "/~ktangwon/bigfile.xyz"
port = 80
timeout = 6

#writeHeader(servName,objName,"header.txt",port,timeout)
#print getHeader("header.txt")[1]
#writeFile(servName,objName,"test.txt",port,"header.txt",timeout)
#NoHeaderFile("test.txt","header.txt")
#print isDL_complete(getHeader("header.txt")[1]["Content-Length"],"test.txt")


