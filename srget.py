import socket as sk 

def mkDownloadRequest(serv, objName):
	return ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n\r\n").format(o=objName, s=serv)

def mkHeadRequest(serv,objName):
	return ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=objName, s=serv)

def writeHeader(serv,objName,header_file,port):
	Head = open(header_file,"w+") # w+ both read and write
	sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
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
	Head.close()

def writeFile(serv,objName,file,port):
	f = open(file,"w+") # w+ both read and write
	sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
	sock.connect((serv,port))
	requestFile = mkDownloadRequest(serv,objName)
	sock.send(requestFile)
	while True:
		data = sock.recv(1024)
		print data,
		if len(data)==0:
			sock.close()
			break
		f.write(data)
		f.close()

def NoHeaderFile(file,header_file):
	f = open(file,"r")
	lines = f.readlines()
	f.close()
	f = open(file,"w")
	header_count = getHeader(header_file)[0]
	print header_count
	count = 0
	for line in lines:
		if count < header_count:
			count += 1
		else:
			f.write(line)
	f.close()

def getHeader(filename):
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

website = "http://www.mahidol.ac.th/en/"
servName ="www.mahidol.ac.th"
objName = "/en/"
port = 80
writeHeader(servName,objName,"header.txt",port)
#print getHeader("header.txt")[1]
#writeFile(servName,objName,"test.txt",port)
#NoHeaderFile("test.txt","header.txt")
