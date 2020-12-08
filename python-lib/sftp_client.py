import paramiko
import json
from stat import S_ISDIR, S_ISREG
import os
import socks # for sock5 
import socket # for  HTTP proxy tunnels
import logging
from base64 import b64encode

logging.basicConfig(loglevel=logging.DEBUG)
LOG = logging.getLogger("dataiku.sftp")

class SftpConnector(object):

    host=None
    port=22
    user=None
    authentication_option=None
    passwd=None
    private_key = None
    sftp=None
    proxy_host=None # if None it assumes no proxy and port is ignored
    proxy_port=1080
    proxy_user=None # if None it assums no authentication 
    proxy_passwd=None
    proxy_command=None
    proxy_option=None



    def __init__(self,sftp_service):
        self.host = sftp_service['hostname'] 
        self.port = sftp_service['port']
        self.user = sftp_service['username']
        self.authentication_option = sftp_service['authentication_option']
        self.passwd = sftp_service.get('password')
        self.private_key = sftp_service.get('private_key')
        self.proxy_option = sftp_service.get("proxy_option")

        # if proxy sock5 available
        if self.proxy_option in  ("sock5", "http") :
            self.proxy_host = sftp_service['proxy_host']
            self.proxy_port = sftp_service['proxy_port']
            self.proxy_user = sftp_service.get('proxy_user')
            self.proxy_passwd = sftp_service.get('proxy_passwd')
        elif self.proxy_option == "proxy_command" :
            self.proxy_command = sftp_service.get('proxy_command')

        self.get_sftp_client()



    def isdir(self,path):
        try:
            return S_ISDIR(self.stat(path).st_mode)
        except IOError:
            raise
            #Path does not exist, so by definition not a directory
        return False

    def isfile(self,path):
        try:
            return S_ISREG(self.stat(path).st_mode)
        except IOError:
            raise
            #Path does not exist, so by definition not a file
        return False


    def sftp_file_exists(self,remote_file):
        sftp = self.get_sftp_client()
        try : 
            self.sftp.stat(remote_file)
            return True
        except IOError as e : 

            return False

        return False



    def get_http_proxy_tunnel(self,timeout=None):

        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.settimeout(timeout)

        headers = {
        }

        # adding basic auth for proxy if available
        if self.proxy_user:
            headers['proxy-authorization'] = 'Basic ' + b64encode('%s:%s' % auth)

        sock.connect((self.proxy_host,self.proxy_port))
        LOG.debug("proxy connected")
        try:
            socket_file = sock.makefile('r+')

            socket_file.write("CONNECT %s:%d HTTP/1.1\r\n" % (self.host,self.port))
            for k,v in headers.items():
                socket_file.write('%s: %s \r\n' % (k, v))
            socket_file.write('\r\n')
            # send socket tunnel opening request 
            LOG.debug("Requesting HTTP tunnel opening")
            socket_file.flush()
            http_protocol, statuscode , message = socket_file.readline().rstrip('\r\n').split(' ', 2)
            statuscode = int(statuscode)

            if statuscode != 200:
                raise IOError("Couldn't connect to %s via proxy: %s (%d) " % (self.host,message,statuscode))
            sock.settimeout(5) 
            while True:
                line = socket_file.readline().rstrip('\r\n')
                if not line:
                    break
                LOG.debug("proxy -> %s" % line)
        except Exception as proxyError :
            socket_file.close()
            sock.close()
            raise proxyError

        socket_file.close()
        return sock


    def get_sock_proxy(self):
        sock = socks.socksocket()
        sock.set_proxy(
            proxy_type=socks.SOCKS5,
            addr=self.proxy_host,
            port=self.proxy_port,
            username=self.proxy_user,
            password=self.proxy_passwd,
        )

        sock.connect((self.host, self.port))
        LOG.debug("proxy connected")
        return sock

    def get_sftp_client(self,force=False):

        if (not force and self.sftp):
            return self.sftp

        if self.proxy_option == 'http':
            LOG.debug("using HTTP Proxy")
            transport = paramiko.Transport(
                self.get_http_proxy_tunnel(timeout=60)
                )
        elif self.proxy_option == 'sock5':
            OG.debug("using Sock Proxy")
            transport = paramiko.Transport(
                self.get_sock_proxy()
                )
        elif (self.proxy_command):
            self.sock = paramiko.ProxyCommand(self.proxy_command)
            transport = paramiko.Transport(self.sock)
        else:
            transport = paramiko.Transport((self.host, self.port))


        if self.authentication_option == "private_key":
            LOG.debug("Connecting with private key authentication")
            mykey = paramiko.RSAKey.from_private_key_file(self.private_key)
            transport.connect(username = self.user,pkey = mykey)
        else:
            LOG.debug("Connecting with password")
            transport.connect(username = self.user, password = self.passwd)

        client = paramiko.SFTPClient.from_transport(transport)
        self.sftp = client
        LOG.debug("type of client "+str(type(client)))
        return client


    # Override paramiko helper with proxy handler
    def open(self,filename,mode="r",bufsize=200):
        LOG.debug("open file:"+filename)
        return self.get_sftp_client().open(
            filename,mode,bufsize=bufsize
            )

    def mkdir(directory):
        self.get_sftp_client().mkdir(directory)
        return

    def rename(previous_file,new_file):
        self.get_sftp_client().rename(previous_file,new_file)
        return

    def stat(path):
        return self.get_sftp_client().stat(path)

    def lstat(path):
        return self.get_sftp_client().lstat(path)

    def listdir(remote_dir):
        return self.get_sftp_client().listdir(remote_dir)

    def remove(path):
        LOG.debug("removing file:"+path)
        self.get_sftp_client().remove(path)
        return

    def rmdir(path):
        LOG.debug("removing directory:"+path)
        self.get_sftp_client().rmdir(path)
        return 

    def rmtree(self,path):
        sftp = self.get_sftp_client()

        if not sftp.sftp_file_exists(path):
            return 
        elif sftp.isdir(path):
            for p in sftp.listdir(path):
                self.rmtree(os.path.join(path,p))
            self.rmdir(path)
        elif sftp.isfile(path):
            sftp.remove(path)
        return

    # Bulk loaders for better performance (from local FS only)
    def upload_dir(self,local_dir,remote_dir):

        files_updated = []
        sftp = self.get_sftp_client()

        if not os.path.exists(local_dir) or not self.sftp_file_exists(remote_dir):
            raise ValueError(local_dir+" and "+ remote_dir+" should exists ")

        if not os.path.isdir(local_dir) or not self.isdir(remote_dir):
            raise ValueError(local_dir+" and "+ remote_dir+" should be directories ")


        print "synking directory %s:%s with %s " % (self.host,remote_dir,local_dir)
        
        local_files =  os.listdir(local_dir)

        for _file in local_files: 

            r_target = os.path.join(remote_dir,_file)
            l_target = os.path.join(local_dir,_file)

            if os.path.isdir(l_target):
                if not self.sftp_file_exists(r_target):
                    sftp.mkdir(r_target)
                files_updated.extend(self.upload_dir(l_target,r_target))
            else :
                l_size = os.path.getsize(l_target)

                if not self.sftp_file_exists(r_target):
                    print (" upload %s  to %s ") % (l_target,r_target)
                    sftp.put(l_target,r_target)
                    files_updated.append(r_target)
                else :
                    attrs = self.stat(r_target)
                    r_size = attrs.st_size
                    try: 
                        if l_size != r_size :
                            print ("update file  %s ...") % r_target
                            sftp.put(l_target,r_target)
                            
                        else:
                            print ("%s is up to date, skipping") % r_target
                        files_updated.append(r_target)
                    except :
                        print ("WARN : could determine overwriting, skipping %s ") % l_target
                        pass 

        try:
            cnx.close()
        except : 
            pass 

        return files_updated


    def download_dir(self,local_dir,remote_dir):

        sftp = self.get_sftp_client()

        if not os.path.exists(local_dir) or not self.sftp_file_exists(remote_dir):
            raise ValueError(local_dir+" and "+ remote_dir+" should exists ")

        if not os.path.isdir(local_dir) or not self.isdir(remote_dir):
            raise ValueError(local_dir+" and "+ remote_dir+" should be directories ")

        print "synking directory %s:%s with %s " % (self.host,remote_dir,local_dir)
        
        remote_files =  sftp.listdir(remote_dir)

        for _file in remote_files: 
            r_target = os.path.join(remote_dir,_file)

            # TODO : Test resolution  --- 
            l_target = os.path.join(local_dir,_file)

            if self.isdir(r_target):
                if not os.path.exists(l_target):
                    os.mkdir(l_target)
                self.download_dir(l_target,r_target)
            else :
                attrs = sftp.stat(r_target)
                r_size = attrs.st_size

                if not os.path.exists(l_target):
                    print ("Downloading  %s ") % r_target
                    sftp.get(r_target,l_target)
                    
                else : 
                    l_size = os.path.getsize(l_target)

                    try: 
                        if l_size != r_size :
                            print ("Downloading %s ...") % _file
                            sftp.get(r_target, l_target)
                            os.rename(_file,l_target)

                    except : 
                        print "WARN : could determine overwriting, skipping ",remote_files
                        pass 

        try:                    
            cnx.close() 
        except : 
            pass 

        return 
