#!usr/bin/env python
import socket as sk 
import os
from urlparse import urlparse

def mkDownloadRequest(serv, objName):
	return ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n\r\n").format(o=objName, s=serv)

def mkHeadRequest(serv,objName):
	return ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=objName, s=serv)

def mkResumeRequest(serv,objName,start,stop):
	return ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-{z}"+"\r\n\r\n").format(o=objName,s=serv,h=str(start),z=str(stop))

def storeURL(url,filename):#store URL in another text file
	f = open("URL"+filename,"w")
	f.write(url)
	f.close()

def writeHeader(serv,objName,header_file,port,timeout): #write header to HEAD + filename
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

def writeFile(serv,objName,filename,port,header_file,timeout): #write file to DL + filename
	size_header = os.stat(header_file).st_size
	content_len = getHeader(header_file)[1]["Content-Length"]
	#print size_header , content_len
	f = open(filename,"w+") # w+ both read and write
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
			if (length-size_header)==int(content_len) and len(data)==0:
				print length-size_header
				sock.close()
				break
			f.write(data)
	except sk.gaierror, e:
		print "Error Connecting to Server"
	except sk.error, ex:
		print "Caught exception socket.error : %s" % ex
	f.close()

def NoHeaderFile(filename,header_file): #split the main file from the header 
	f = open(file,"r")
	lines = f.readlines()
	f.close()
	f = open(filename,"w")
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

def isDL_complete(header_File,filename): #check if download is complete
	C_len = getHeader(header_File)[1]["Content-Length"]
	info = os.stat(filename)
	print C_len, info.st_size
	return info.st_size == int(C_len)

def resumeDL(serv,path,old_file,temp_file,new_header,timeout):
	#start at old file size
	#end at content length
	size_oldfile = os.stat(old_file).st_size #start
	size_header = os.stat(new_header).st_size 
	content_len = getHeader(new_header)[1]["Content-Length"] #stop
	#print size_header , content_len
	f = open(temp_file,"w+") # w+ both read and write
	sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
	sock.settimeout(timeout)
	try:
		sock.connect((serv,port))
		requestFile = mkResumeRequest(serv,path,size_oldfile,content_len)
		sock.send(requestFile)
		length = 0
		while True:
			data = sock.recv(1024)
			length += len(data)
			if (length-size_header)==int(content_len) and len(data)==0:
				print length-size_header
				sock.close()
				break
			f.write(data)
	except sk.gaierror, e:
		print "Error Connecting to Server"
	except sk.error, ex:
		print "Caught exception socket.error : %s" % ex
	f.close()
	#Remove header
	NoHeaderFile(temp_file,new_header)
	#Append to first file
	filenames = [old_file,temp_file]
	with open('path/to/output/file', 'w') as outfile:
	    for fname in filenames:
	        with open(fname) as infile:
	            for line in infile:
	                outfile.write(line)

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
		check_url = f.readlines()[0]
		if url==check_url:#check if the same URL
			writeHeader(Host_serv,Host_path,"NEWHEAD"+filename,Host_port,timeout)
			new_info = getHeader("NEWHEAD"+filename)
			old_info = getHeader("HEAD"+filename)
			Changed = False
			if "Etag" in (new_info[1] and old_info[1]):
				if new_info[1]["Etag"]!=old_info[1]["Etag"]:
					Changed = True
			elif "Last-Modified" in (new_info[1] and old_info[1]):
				if new_info[1]["Last-Modified"]!=old_info[1]["Last-Modified"]:
					Changed = True
			if Changed:
				print "Redownload"
			else:
				print "Resume"
		else: # Overwrite the file, the header file, the URL file
			print "Overwrite"

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
		writeHeader(Host_serv,Host_path,"HEAD"+filename,Host_port,timeout)
		a = open("HEAD"+filename,"r")
		http_line =  a.readlines()[0]
		print http_line
		if http_line == "HTTP/1.1 200 OK\r\n":
			storeURL(url,filename)
			writeFile(Host_serv,Host_path,"DL"+filename,Host_port,"HEAD"+filename,timeout)
			NoHeaderFile("DL"+filename,"HEAD"+filename)
			isComplete = isDL_complete("HEAD"+filename,"DL"+filename)
			print isComplete
			if isComplete:
				os.remove("HEAD"+filename)
				os.remove("URL"+filename)
				os.rename("DL"+filename,filename)
				return "File Downloaded"
		else:
			return "error: ", http_line



website = "http://cs.muic.mahidol.ac.th/~ktangwon/bigfile.xyz"
servName ="cs.muic.mahidol.ac.th"
objName = "/~ktangwon/bigfile.xyz"
port = 80
timeout = 6

#print main("test.txt","http://cs.muic.mahidol.ac.th/~ktangwon/bigfile.xyz")
writeHeader(servName,objName,"header.txt",port,timeout)
#print getHeader("header.txt")[1]
#writeFile(servName,objName,"test.txt",port,"header.txt",timeout)
#NoHeaderFile("test.txt","header.txt")
#print isDL_complete("header.txt","test.txt")


