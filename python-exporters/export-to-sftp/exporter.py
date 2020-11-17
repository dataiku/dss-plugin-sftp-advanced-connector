# -*- coding: utf-8 -*-
from dataiku.exporter import Exporter
from dataiku.exporter import SchemaHelper
import tempfile, os
from sftp_client import SftpConnector
import csv


class CustomExporter(Exporter):

    def __init__(self, config, plugin_config):
        #read config
        self.config = config
        self.plugin_config = plugin_config
        self.sftp_service = config.get('sftpService')
        self.sftp_root_path = config.get('sftp_root_path')
        self.filename = config.get('filename')
        self.delimiter = config.get('delimiter')
        self.set_headers = config.get("headers")
        self.bufsize = config.get('bufsize')
        self.sftp = SftpConnector(self.sftp_service)
        return
        

    def open(self, schema):
        if not self.sftp.isdir(self.sftp_root_path):
            raise ValueError('Directory {} does not exist on server'.format(self.sftp_root_path))

        target_file = os.path.join(self.sftp_root_path,self.filename)
        self.openedFile = self.sftp.open(target_file,mode="w",bufsize=self.bufsize)
        self.writer = csv.writer(self.openedFile, delimiter=str(self.delimiter), quotechar='"', quoting=csv.QUOTE_MINIMAL)

        print "headers ",self.set_headers
        if self.set_headers:
            header = []
            for col in schema.get("columns"):
                header.append(str(col.get("name")))

            self.writer.writerow(header)

        return


    def write_row(self, row):
        """
        Handle one row of data to export
        :param row: a tuple with N strings matching the schema passed to open.
        """
        self.writer.writerow(row)
        return
        
        
    def close(self):
        self.openedFile.close()
        return





