from socket import *
import socket
import socket as sk
import sys, getopt, pickle, os, asyncore
from urlparse import urlparse
import logging
# from cStringIO import StringIO

 #split the main file from the header
def NoHeaderFile(filename,header_line): 
    f = open(filename,"r")
    lines = f.readlines()
    f.close()
    f = open(filename,"w")
    header_count = header_line
    count = 0
    for line in lines:
        if count < header_count:
            count += 1
        else:
            f.write(line)
    f.close()

#download handle with and without content length
def download_file(serv,objName,filename,port,header_info,request,og_contentL): 
    sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
    size_header = header_info['size']
    header_line = header_info['count']
    content_len = header_info['Content-Length']
    length = 0
    try:
        sock.connect((serv,port))
    except sk.error, e:
        print "Connection Error"
        sys.exit(1)
    f = open(filename,"w+")
    sock.send(request)
    try:
        while True:
            data = sock.recv(1024)
            length += len(data)
            # print length-size_header
            if (length-size_header)==int(content_len): #receive data until it meets the content length
                sock.close()
                f.write(data)
                break
            f.write(data)
        f.close()

    except sk.error: #handle and remove the appropriate files
            sock.close()
            f.close()
            NoHeaderFile(filename,header_line)
            print "Error receiving content from server"
            if filename[:3] == "NEW":
                append_file("DL"+filename[3:],filename)
                a = os.path.getsize("DL"+filename[3:])
            else:
                a = os.path.getsize(filename)
            print str((a/float(og_contentL))*100) + "% DOWNLOADED"
            sys.exit(1)
    except KeyboardInterrupt:
            sock.close()
            f.close()
            NoHeaderFile(filename,header_line)
            print filename
            print "DL"+filename[3:]
            if filename[:3] == "NEW":
                append_file("DL"+filename[3:],filename)
                a = os.path.getsize("DL"+filename[3:])
            else:
                a = os.path.getsize(filename)
            print str((a/float(og_contentL))*100) + "% DOWNLOADED"
            sys.exit(1)
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

def download(filename,header_info,serv,path,port,request_dl,og_contentL):
    header_line = header_info['count']
    content_len = header_info['Content-Length']
    download_file(serv,path,filename,port,header_info,request_dl,og_contentL) #download file
    NoHeaderFile(filename,header_line) # separate header from file
    if isDL_complete(og_contentL,filename): #handle the files needed to be removed
        return "DOWNLOAD COMPLETED"

def append_file(original,new):
    f_old = open(original,"a+")
    f_new = open(new,"r")
    for line in f_new:
        f_old.write(line)
    f_old.close()
    f_new.close()
    os.remove(new) #combine two files

def one_connection(url,filename): #One connection
    parsed = urlparse(url)
    Host_serv = parsed.netloc
    Host_path = parsed.path
    Host_port = parsed.port
    toRedirect = False
    toOverwrite = ""
    if Host_port == None:
        Host_port = 80

    if os.path.exists("DL"+filename): #if partially downloaded filename exists

        with open(filename+'.pickle','rb') as handle:
            head = pickle.load(handle) ## original header

        og_url = head['url'] #original url
        og_contentL = head['Content-Length']

        if url==og_url: #check if same url
            start = os.path.getsize("DL"+filename) #byte to resume from
            #Resume requests
            resumeHead = ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-"+"\r\n\r\n").format(o=Host_path,s=Host_serv,h=str(start))
            resumeReq = ("GET {o} HTTP/1.1\r\n"+"Host: {s}\r\n"+"Range: bytes={h}-"+"\r\n\r\n").format(o=Host_path,s=Host_serv,h=str(start))

            #Get new header and old header to compare
            Download_Header(Host_serv,Host_path,"NEWHEAD"+filename,Host_port,resumeHead)
            new_header_info = get_header("NEWHEAD"+filename,url) #dct of info

            # Check using ETags and Last modified to see if the file has changed
            if "ETag" in new_header_info and "ETag" in head: #head --> old header info
                if new_header_info["ETag"] == head["ETag"]:
                    print "NOT MODIFIED: Resuming Download"
                    download("NEW"+filename,new_header_info,Host_serv,Host_path,Host_port,resumeReq,og_contentL)
                    append_file("DL"+filename,"NEW"+filename)
                    #download complete rem pickle and rename DLfile
                    os.remove(filename+'.pickle')
                    os.rename("DL"+filename,filename)
                    return "Resumed Download Complete"

            elif ("Last-Modified" in new_header_info) and ("Last-Modified" in old_header_info):
                if new_header_info["Last-Modified"] == head["Last-Modified"]:
                    print "NOT MODIFIED: Resuming Download"
                    download("NEW"+filename,new_header_info,Host_serv,Host_path,Host_port,resumeReq,og_contentL)
                    append_file("DL"+filename,"NEW"+filename)
                    os.remove(filename+'.pickle')
                    os.rename("DL"+filename,filename)
                    return "Resumed Download Complete"

            #if it fails ETag and Last-Modified test
            print "Restarting Download"
            if os.path.exists("DL"+filename):
                os.remove("DL"+filename)
            if os.path.exists(filename+'.pickle'):
                os.remove(filename+'.pickle')

    elif os.path.exists(filename): #if same file name exists : chose to overwrite
        print "File exists: Do you want to overwrite the file?"
        while True:
            toOverwrite = raw_input("Do you want to overwrite the file? (Y/N) :") 
            if toOverwrite.upper() == "N":
                return "Please choose a new filename."
            elif toOverwrite.upper() == "Y":
                break
        os.remove(filename)

    ### if need to restart download again
    ### if overwrite is chosen or filename does not exist
    print "DOWNLOADING"

    request_head = ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=Host_path, s=Host_serv)
    Download_Header(Host_serv,Host_path,"HEAD"+filename,Host_port,request_head)
    print 'here'
    head_info = get_header("HEAD"+filename,url) #header will be removed in get_header

    with open(filename+'.pickle','wb') as handle:
        pickle.dump(head_info,handle)

    request_dl = ("GET {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=Host_path, s=Host_serv)
    print head_info['Content-Length']
    download("DL"+filename,head_info,Host_serv,Host_path,Host_port,request_dl,head_info['Content-Length'])

    #when download complete remove pickle file and rename DL+filename
    os.remove(filename+'.pickle')
    os.rename("DL"+filename,filename)
    return "DOWNLOAD COMPLETE"
def Download_Header(serv,objName,filename,port,request):
    temp = open(filename,"w+")
    sock = sk.socket(sk.AF_INET,sk.SOCK_STREAM)
    try:#try to connect
        sock.settimeout(5)
        sock.connect((serv,port))
    except sk.error, e:
        print  "Connection error"
        os.remove(filename)
        sys.exit(1)
    except sk.gaierror:
        print "Connection Timed Out"
        sys.exit(1)
    except KeyboardInterrupt:
        os.remove(filename)
        sys.exit(1)
    try:#try to send request
        sock.send(request)
    except sk.error:
        os.remove(filename)
        print "Error sending server request"
        sys.exit(1)

    data = ""
    while True:
        try: #try to receive information
            data += sock.recv(1024)
        except sk.error:
            print "Error receiving header from server"
            os.remove(filename)
            sys.exit(1)
        except KeyboardInterrupt:
            os.remove(filename)
            sys.exit(1)
        if data[len(data)-4:len(data)] == "\r\n\r\n":
            sock.close()
            break
    temp.write(data)
    temp.close()

#store header info in dct and remove header file
def get_header(filename,url): 
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
    dct['count'] = count
    dct['size'] = os.path.getsize(filename)
    if url != None:
        dct['url'] = url
    os.remove(filename)
    return dct

class HTTPClient(asyncore.dispatcher):
    def __init__(self,filename,pos, host, path,port,header_info,range_byte):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.filename = filename
        self.pos = pos
        # self.recvbuf = ""
        self.logger = logging.getLogger(host+path)
        self.sendbuf = ""
        self.header = ""
        self.range_byte = range_byte
        self.header_info = header_info #header info get content_len count
        self.wait_header = True
        self.port = port
        try:
            self.connect((host, port))
        except:
            print 'Connection Error'
            sys.exit(1)
        # self.buffer = 'GET %s HTTP/1.1\r\nHost: %s \r\nRange: %s\r\nConnection: close \r\n\r\n' % (path, host, range_byte)
        self.buffer = 'GET %s HTTP/1.1\r\nHost: %s \r\nRange: %s\r\nConnection: close \r\n\r\n' % (path, host, range_byte)
        ## make my request
        # self.write(make_request('GET', path,{"host": host,"Connection":'close'}))#"Range": self.range_
 
    def handle_connect(self):#when connected event
        self.logger.debug("connection established")
        # print 'START',self.pos
        pass
 
    def handle_close(self):#when connection close
        self.logger.debug("got disconnected")
        # print 'END', self.pos
        self.close()

    def handle_read(self):
        buf = self.recv(8192)
        self.filename.seek(self.pos)
        # print self.pos
        if self.wait_header and '\r\n\r\n' in buf:
            self.wait_header = False
            end_head = buf.find('\r\n\r\n') + 4
            # self.recvbuf += buf[end_head:]
            self.filename.write(buf[end_head:])
            self.pos +=len(buf[end_head:])
        elif self.wait_header:
            self.header +=buf
        else:
            # self.recvbuf += buf
            self.filename.write(buf)
            self.pos += len(buf)
        # self.logger.debug("recv {0} bytes".format(len(buf)))

    def writeable(self):
        return len(self.buffer) > 0
 
    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

logging.basicConfig(level=logging.DEBUG,format="%(asctime)-15s %(name)s: %(message)s")

def gap(length): #split length of file into N partition
    lst = []
    if length <= 1258291:
        each = length/2
        r = 2

    if length > 1258291 and length <= 5679102:
        each = length/4
        r = 4

    if length > 5679102 and length<= 10345678:
        each = length/5
        r = 5

    if length > 10345678 and length <= 103956789:
        each = length/7
        r = 7

    if length >= 103956789 and length < 529956789:
        each = length/14
        r = 14

    if length >= 529956789:
        each = length/16
        r = 16

    if length >= 1090000000:
        each = length/18
        r = 18

    # each = length/N
    start = 0
    for i in range(r-1):
        # lst.append([start,(start + each)])
        lst.append([start,(start + each)-1])
        start += each
    lst.append([start,length])
    return lst

def divide_gap(gap,num_conn):
    dif = gap[1] - gap[0]
    each = dif/num_conn
    lst = []
    start = gap[0]
    for i in range(num_conn-1):
        lst.append([start,(start+each)-1])
        start+=each
    lst.append([start,gap[1]])
    return lst

def make_range(gap):
    lst= []
    for i in gap:
        st = ('bytes={s}-{e}').format(s=str(i[0]),e=str(i[1]))
        lst.append(st)
    return lst


def n_connections(url,filename,connections):
    #For recursive purposes
    URL = url
    fn = filename
    conn = connections
    ##################
    parsed = urlparse(url)
    Host_serv = parsed.netloc
    Host_path = parsed.path
    Host_port = parsed.port
    if Host_port == None:
        Host_port = 80
    else:
        Host_serv = Host_serv[:-len(str(Host_port))-1]

    #Get header first to check if valid to download
    request_head = ("HEAD {o} HTTP/1.1\r\n"+"Host: {s}" +"\r\n\r\n").format(o=Host_path, s=Host_serv)
    Download_Header(Host_serv,Host_path,'HEAD'+filename,Host_port,request_head)
    dct = get_header('HEAD'+filename,url)
    # print dct['Content-Length']

    if 'Content-Length' not in dct:
        return 'No Content Length, can only use 1 connection.'

    content_len = dct['Content-Length']

    if os.path.exists('DL' +filename): #partially downloaded filename

        if os.path.exists(filename+',pickle'):
            with open(filename+'.pickle','r') as handle:
                res = pickle.load(handle)
        else:
            os.remove('DL'+filename)
            return 'Cannot Resume: file components missing'
        
        header_ = res['header']
        gap_count = res['gap']
        part = res['part']
        if header_['url'] == url:
            if "ETag" in header_ and "ETag" in dct: #head --> old header info
                if header_["ETag"] == dct["ETag"]:
                    fo = open('DL'+filename,'r+b')
                    Gap= [divide_gap(j,connections) for j in part[gap_count:]]
                    ranges = [make_range(i) for i in Gap]
                    clients = []
                    for xd,i in enumerate(ranges): # go through the range
                        pos = [it[0] for it in Gap[xd]] #Get the right Gap for pos
                        for idx,j in enumerate(i):
                            clients.append(HTTPClient(fo,pos[idx],Host_serv,Host_path,Host_port,dct,j))
                        try:
                            asyncore.loop()
                            gap_count += 1
                            client = []
                            to_dump = {'header':dct,'gap':gap_count,'part':part}
                            with open(filename+'.pickle','w') as handle:
                                pickle.dump(to_dump,handle)
                        except:
                            print 'Download interrupted'
                            sys.exit(1)

                    if gap_count == len(part):
                        os.rename('DL'+filename,filename)
                        if os.path.exists(filename+'.pickle'):
                            os.remove(filename+'.pickle')
                        return 'Download Completed'

            elif "Last-Modified" in header_ and "Last-Modified" in dct: #head --> old header info
                if header_["Last-Modified"] == dct["Last-Modified"]:
                    fo = open('DL'+filename,'r+b')
                    Gap= [divide_gap(j,connections) for j in part[gap_count:]]
                    ranges = [make_range(i) for i in Gap]
                    clients = []
                    for xd,i in enumerate(ranges): # go through the range
                        pos = [it[0] for it in Gap[xd]] #Get the right Gap for pos
                        for idx,j in enumerate(i):
                            clients.append(HTTPClient(fo,pos[idx],Host_serv,Host_path,Host_port,dct,j))
                        try:
                            asyncore.loop()
                            gap_count += 1
                            client = []
                            to_dump = {'header':dct,'gap':gap_count,'part':part}
                            with open(filename+'.pickle','w') as handle:
                                pickle.dump(to_dump,handle)
                        except:
                            print 'Download interrupted'
                            sys.exit(1)

                    if gap_count == len(part):
                        os.rename('DL'+filename,filename)
                        if os.path.exists(filename+'.pickle'):
                            os.remove(filename+'.pickle')
                        return 'Download Completed'

            print 'File was modified, please restart download'
            if os.path.exists('DL'+filename):
                os.remove('DL'+filename)
            if os.path.exists(filename+'.pickle'):
                os.remove(filename+'.pickle')
            n_connections(URL,fn,conn)


    elif os.path.exists(filename):
        return '---Choose a new filename---'

    else:#Download page with given connections
        open('DL'+filename, 'a').close()
        fo = open('DL'+filename,'r+b')
        part = gap(int(content_len)) #gaps
        Gap= [divide_gap(j,connections) for j in part] #position for using seek
        ranges = [make_range(i) for i in Gap]
        gap_count = 0
        clients = []
        for xd,i in enumerate(ranges): # go through the range
            pos = [it[0] for it in Gap[xd]] #Get the right Gap for pos
            for idx,j in enumerate(i):
                clients.append(HTTPClient(fo,pos[idx],Host_serv,Host_path,Host_port,dct,j))
            try:
                asyncore.loop()
                gap_count += 1
                client = []
                to_dump = {'header':dct,'gap':gap_count,'part':part}
                with open(filename+'.pickle','w') as handle:
                    pickle.dump(to_dump,handle)
            except:
                print 'Download interrupted'
                sys.exit(1)
                
        fo.close()
        if os.path.getsize('DL'+filename)==int(content_len):
            os.rename('DL'+filename,filename)
            if os.path.exists(filename+'.pickle'):
                os.remove(filename+'.pickle')
            return 'Download Complete'


# print n_connections('http://cs.muic.mahidol.ac.th/~ktangwon/bigfile.xyz','test1.xyz',10)

# print one_connection('http://cs.muic.mahidol.ac.th/~ktangwon/bigfile.xyz','test2.xyz')

