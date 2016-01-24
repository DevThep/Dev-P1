import socket as sk 
import os
import sys
from urlparse import urlparse

def storeURL(url,filename):#store URL in another text file
	f = open(filename,"w")
	f.write(url)
	f.close()

def NoHeaderFile(filename,header_line): #split the main file from the header 
	f = open(filename,"r")
	lines = f.readlines()
	f.close()
	f = open(filename,"w")
	header_count = header_line
	#print header_count
	count = 0
	for line in lines:
		if count < header_count:
			count += 1
		else:
			f.write(line)
	f.close()

def Download_Header(serv,objName,filename,port,request): #RETURN: header line count, dictionary of header elements
	temp = open(filename,"w+")
	sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
	try:#try to connect
		sock.connect((serv,port))
	except sk.error, e:
		print  "Connection error"
		os.remove(filename)
		sys.exit(1)

	try:#try to send request
		sock.send(request)
	except sk.error:
		print "Error sending server request"

	data = ""
	while True:
		try: #try to receive information
			data += sock.recv(1024)
		except sk.error:
			print "Error receiving header from server"
			os.remove(filename)
			sys.exit(1)
		if data[len(data)-4:len(data)] == "\r\n\r\n":
			sock.close()
			break
	temp.write(data)
	temp.close()

def get_header(filename):
	t = open(filename)
	dct = dict()
	count = 0
	for line in t.readlines():
		if count == 0:
			count += 1
			continue
		elif line != "\r\n":
			separate = line.split(":",1)
			dct[separate[0]] = separate[1][1:len(separate[1])-2]
		count += 1
	t.close()
	return count, dct, os.path.getsize(filename)

def download_file(serv,objName,filename,port,header_file,isContentLen,request):
	header_info = get_header(header_file)
	size_header = header_info[2]
	#print size_header , content_len
	 # w+ both read and write
	sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
	try:
		sock.connect((serv,port))
	except sk.error, e:
		print "Connection Error"
		sys.exit(1)
	f = open(filename,"w+")
	sock.send(request)
	#print isContentLen 
	if isContentLen != None: #If Content Length exists
		content_len = isContentLen
		#print content_len
		length = 0
		try:
			while True:
				data = sock.recv(1024)
				length += len(data)
				print length-size_header
				if (length-size_header)==int(content_len):
					#print length-size_header
					sock.close()
					f.write(data)
					break
				f.write(data)
			f.close()

		except sk.error:
			sock.close()
			f.close()
			NoHeaderFile(filename,get_header(header_file)[0])
			if filename[:3] == "NEW":
				append_file("DL"+filename[3:],filename)
			if header_file[:3]=="NEW":
				os.remove(header_file)
			print "Error receiving content from server"
			a = float(content_len)
			b = os.path.getsize("DL"+filename[3:])
			print str((b/a)*100) + "% DOWNLOADED"
			sys.exit(1)

		except KeyboardInterrupt:
			sock.close()
			f.close()
			NoHeaderFile(filename,get_header(header_file)[0])
			if filename[:3] == "NEW":
				append_file("DL"+filename[3:],filename)
			if header_file[:3]=="NEW":
				os.remove(header_file)
			print "User stopped download"
			print "\n"+filename
			a = float(content_len)
			if filename[:3] != "NEW":
				b = os.path.getsize("DL"+filename[2:])
			else:
				b = os.path.getsize("DL"+filename[3:])
			print str((b/a)*100) + "% DOWNLOADED"
			sys.exit(1)
			
	else:#download till last 0
		data = ""
		try:
			while True:
				data += sock.recv(1024)
				if "0\r\n\r\n" in data:
					sock.close()
					f.write(data)
					break
				f.write(data)
		except sk.error:
			print "The url requested has no content length\n Have to restart the download!"
			f.close()				
			os.remove(filename)
			sys.exit(1)
		except KeyboardInterrupt:
			print "The url requested has no content length\n Have to restart the download!"
			f.close()				
			os.remove(filename)
			sys.exit(1)
		return "DOWNLOAD COMPLETED"
	f.close()

def check_http(header_file):
	f = open(header_file,"r")
	a = f.readlines()[0]
	status = a[9:12]
	if int(status) >= 200 and int(status) <= 206:
		return "Successful 2xx"
	elif int(status) >= 300 and int(status) <= 307:
		return "Redirection 3xx"
	elif int(status) >= 400 and int(status) <= 417:
		return "Client Error 4xx"
	elif int(status) >= 500 and int(status) <= 505:
		return "Server Error 5xx"
	f.close()

def isDL_complete(contentL,filename): #check if download is complete
	return os.path.getsize(filename)==int(contentL)

def download(filename,header_file,serv,path,port,contentL,header_req,request_dl,url):
	if "Content-Length" in get_header(header_file)[1]:
		contentL = get_header(header_file)[1]["Content-Length"]
	download_file(serv,path,filename,port,header_file,contentL,request_dl)
	NoHeaderFile(filename,get_header(header_file)[0])
	if contentL != None:
		if isDL_complete(contentL,filename):
			if os.path.exists("NEWHEAD"+filename):
				os.remove("NEWHEAD"+filename)
			os.remove(header_file)
			return "DOWNLOAD COMPLETED"
	else: #Case for NO CONTENT LENGTH
		os.remove(header_file)
		os.remove("URL"+filename[2:])
		os.rename(filename,filename[2:])
		print "DOWNLOAD COMPLETE"
		sys.exit(1)

def append_file(original,new):
	f_old = open(original,"a+")
	f_new = open(new,"r")
	for line in f_new:
		f_old.write(line)
	f_old.close()
	f_new.close()
	os.remove(new)

def main(url,filename):
	parsed = urlparse(url)
	Host_serv = parsed.netloc
	Host_path = parsed.path
	Host_port = parsed.port
	toRedirect = False
	toOverwrite = ""
	if Host_port == None:
		Host_port = 80

	if os.path.exists("DL"+filename): #if partially downloaded filename exists
		f = open("URL"+filename,"r")
		check_url = f.readlines()[0]
		f.close()
		print check_url
		if url==check_url: #same url

			start = os.path.getsize("DL"+filename) #byte to resume from
			resumeHead = ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-"+"\r\n\r\n").format(o=Host_path,s=Host_serv,h=str(start))
			resumeReq = ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-"+"\r\n\r\n").format(o=Host_path,s=Host_serv,h=str(start))
			#Get new header
			Download_Header(Host_serv,Host_path,"NEWHEAD"+filename,Host_port,resumeHead)
			new_header_info = get_header("NEWHEAD"+filename)[1]
			old_header_info = get_header("HEAD"+filename)[1]

			if "ETag" in new_header_info and "ETag" in old_header_info:
				if new_header_info["ETag"] == old_header_info["ETag"]:
					print "NOT MODIFIED: Resuming Download"
					download("NEW"+filename,"NEWHEAD"+filename,Host_serv,Host_path,Host_port,None,resumeHead,resumeReq,url)
					append_file("DL"+filename,"NEW"+filename)
					if os.path.exists("URL"+filename):
						os.remove("URL"+filename)
					if os.path.exists("HEAD"+filename):
						os.remove("HEAD"+filename)
					os.rename("DL"+filename,filename)
					print "Resumed Download Complete"
					return "Resumed Download Complete"

			elif ("Last-Modified" in new_header_info) and ("Last-Modified" in old_header_info):
				if new_header_info["Last-Modified"] == old_header_info["Last-Modified"]:
					return "NOT MODIFIED: Resuming Download"
			else:
				print "Restarting Download"
			#contentL = get_header("new_header.txt")[1]["Content-Length"]
			#download_file(serv,page,"res_file.txt",80,"new_header.txt",contentL,resumeReq)
			#NoHeaderFile("res_file.txt",get_header("new_header.txt")[0])
		return

	elif os.path.exists(filename): #if same file name exists : chose to overwrite
		print "File exists: Do you want to overwrite the file?"
		while True:
			toOverwrite = raw_input("Do you want to overwrite the file? (Y/N) :") 
			if toOverwrite.upper() == "N":
				return "Please choose a new filename."
			elif toOverwrite.upper() == "Y":
				break
		os.remove(filename)

	### if overwrite is chosen or filename does not exist
	print "DOWNLOADING"
	request_head = ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=Host_path, s=Host_serv)
	Download_Header(Host_serv,Host_path,"HEAD"+filename,Host_port,request_head)
	request_dl = ("GET {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=Host_path, s=Host_serv)
	storeURL(url,"URL"+filename)
	download("DL"+filename,"HEAD"+filename,Host_serv,Host_path,Host_port,None,request_head,request_dl,url)
	os.remove("URL"+filename)
	os.rename("DL"+filename,filename)
	return "DOWNLOAD COMPLETE"

# print main("http://math.hws.edu/eck/cs124/downloads/javanotes6-linked.pdf","java.pdf")
print main("http://images.clipartpanda.com/lion-clipart-for-kids-lion-clip-art_1404121345.jpg","lion.jpg")
# website = "http://images.clipartpanda.com/lion-clipart-for-kids-lion-clip-art_1404121345.jpg"
#website = "http://cs.muic.mahidol.ac.th/~ktangwon/bigfile.xyz"
#website = "http://math.hws.edu/eck/cs124/downloads/javanotes6-linked.pdf"
# serv = "cs.muic.mahidol.ac.th"
# page = "/~ktangwon/bigfile.xyz"
# serv = "www.google.co.th"
# page = "/?gws_rd=cr&ei=HIGkVqvYLI6gugThzLuYDw"
# serv = "math.hws.edu"
# page = "/eck/cs124/downloads/javanotes6-linked.pdf"

# request = ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=page, s=serv)
# download_req = ("GET {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=page, s=serv)
# Download_Header(serv,page,"header.txt",80,request)
#contentL = get_header("header.txt")[1]["Content-Length"]
#download_file(serv,page,"file.txt",80,"header.txt",contentL,download_req)
#NoHeaderFile("file.txt",get_header("header.txt")[0])
#print os.path.getsize("file.txt")

#start = os.path.getsize("file.txt")
#print start
#resumeHead = ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-"+"\r\n\r\n").format(o=page,s=serv,h=str(start))
#resumeReq = ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-"+"\r\n\r\n").format(o=page,s=serv,h=str(start))
#Download_Header(serv,page,"new_header.txt",80,resumeHead)
#contentL = get_header("new_header.txt")[1]["Content-Length"]
#download_file(serv,page,"res_file.txt",80,"new_header.txt",contentL,resumeReq)
#NoHeaderFile("res_file.txt",get_header("new_header.txt")[0])
#print get_header("header.txt")[1]["Content-Length"]
#print os.path.getsize("file.txt") + os.path.getsize("res_file.txt")