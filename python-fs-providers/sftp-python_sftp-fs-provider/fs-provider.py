# This file is the actual code for the custom Python FS provider sftp-python_sftp-fs-provider

from dataiku.fsprovider import FSProvider
import os, shutil
import tempfile
from sftp_client import SftpConnector

"""
This sample provides files from inside the providerRoot passed in the config
"""
class CustomFSProvider(FSProvider):
    def __init__(self, root, config, plugin_config):
        """
        :param root: the root path for this provider
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        if len(root) > 0 and root[0] == '/':
            root = root[1:]
        self.root = root

        self.sftp_service = config.get('sftpService')
        self.sftp_root_path = config.get('sftp_root_path')

        self.bufsize = config.get('bufsize')
        self.sftp = SftpConnector(self.sftp_service)

    # util methods
    def get_rel_path(self, path):
        if len(path) > 0 and path[0] == '/':
            path = path[1:]
        return path
    def get_lnt_path(self, path):
        if len(path) == 0 or path == '/':
            return '/'
        elts = path.split('/')
        elts = [e for e in elts if len(e) > 0]
        return '/' + '/'.join(elts)
    def get_full_path(self, path):
        path_elts = [self.sftp_root_path, self.get_rel_path(self.root), self.get_rel_path(path)]
        path_elts = [e for e in path_elts if len(e) > 0]
        return os.path.join(*path_elts)

    def close(self):
        """
        Perform any necessary cleanup
        """
        print ('close')

    def stat(self, path):
        """
        Get the info about the object at the given path inside the provider's root, or None 
        if the object doesn't exist
        """
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            return None
        if os.path.isdir(full_path):
            return {'path': self.get_lnt_path(path), 'size':0, 'lastModified':int(os.path.getmtime(full_path)) * 1000, 'isDirectory':True}
        else:
            return {'path': self.get_lnt_path(path), 'size':os.path.getsize(full_path), 'lastModified':int(os.path.getmtime(full_path)) * 1000, 'isDirectory':False}
            
    def set_last_modified(self, path, last_modified):
        """
        Set the modification time on the object denoted by path. Return False if not possible
        """
        full_path = self.get_full_path(path)
        os.utime(full_path, (os.path.getatime(full_path), last_modified / 1000))
        return True
        
    def browse(self, path):
        """
        List the file or directory at the given path, and its children (if directory)
        """
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            return {'fullPath' : None, 'exists' : False}
        elif os.path.isfile(full_path):
            return {'fullPath' : self.get_lnt_path(path), 'exists' : True, 'directory' : False, 'size' : os.path.getsize(full_path)}
        else:
            children = []
            for sub in os.listdir(full_path):
                sub_full_path = os.path.join(full_path, sub)
                sub_path = self.get_lnt_path(os.path.join(path, sub))
                if os.path.isdir(sub_full_path):
                    children.append({'fullPath' : sub_path, 'exists' : True, 'directory' : True, 'size' : 0})
                else:
                    children.append({'fullPath' : sub_path, 'exists' : True, 'directory' : False, 'size' : os.path.getsize(sub_full_path)})
            return {'fullPath' : self.get_lnt_path(path), 'exists' : True, 'directory' : True, 'children' : children}
            
    def enumerate(self, path, first_non_empty):
        """
        Enumerate files recursively from prefix. If first_non_empty, stop at the first non-empty file.
        
        If the prefix doesn't denote a file or folder, return None
        """
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            return None
        if os.path.isfile(full_path):
            return [{'path':self.get_lnt_path(path), 'size':os.path.getsize(full_path), 'lastModified':int(os.path.getmtime(full_path)) * 1000}]
        paths = []
        for root, dirs, files in os.walk(full_path):
            for file in files:
                full_sub_path = os.path.join(root, file)
                sub_path = full_sub_path[len(os.path.join(self.sftp_root_path, self.root)):]
                paths.append({'path':self.get_lnt_path(sub_path), 'size':os.path.getsize(full_sub_path), 'lastModified':int(os.path.getmtime(full_sub_path)) * 1000})
        return paths
        
    def delete_recursive(self, path):
        """
        Delete recursively from path. Return the number of deleted files (optional)
        """
        full_path = self.get_full_path(path)
        if not os.path.exists(full_path):
            return 0
        elif os.path.isfile(full_path):
            os.remove(full_path)
            return 1
        else:
            shutil.rmtree(full_path)
            return 0
            
    def move(self, from_path, to_path):
        """
        Move a file or folder to a new path inside the provider's root. Return false if the moved file didn't exist
        """
        full_from_path = self.get_full_path(from_path)
        full_to_path = self.get_full_path(to_path)
        if self.sftp.sftp_file_exists(full_from_path):
            if from_path != to_path:
                self.sftp.rename(full_from_path, full_to_path)
            return True
        else:
            return False
            
    def read(self, path, stream, limit):
        """
        Read the object denoted by path into the stream. Limit is an optional bound on the number of bytes to send
        """
        full_path = self.get_full_path(path)
        if not self.sftp.sftp_file_exists(full_path):
            raise Exception('Path doesn t exist')
        with self.sftp.open(target_file,mode="r",bufsize=self.bufsize) as f:
            shutil.copyfileobj(f, stream,self.bufsize)

        return
            
    def write(self, path, stream):
        """
        Write the stream to the object denoted by path into the stream
        """
        full_path = self.get_full_path(path)
        full_path_parent = os.path.dirname(full_path)

        if not self.sftp.sftp_file_exists(full_path_parent):
            self.sftp.mkdir(full_path_parent)

        self.openedFile = self.sftp.open(full_path,mode="w",bufsize=self.bufsize)
        with self.sftp.open(target_file,mode="wb",bufsize=self.bufsize) as f:
            shutil.copyfileobj(stream, f,self.bufsize)
