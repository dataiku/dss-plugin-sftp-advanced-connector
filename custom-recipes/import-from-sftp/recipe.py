# -*- coding: utf-8 -*-
import dataiku
from dataiku.customrecipe import *
import json
from sftp_client import SftpConnector


print ("Custom Recipe being")

# get recipe config
sftp_service = get_recipe_config()['sftpService']
sftp_root_path = get_recipe_config()['sftp_root_path']

# Load connector from  python-lib
sftp_connector = SftpConnector(sftp_service)

# get the full location of local folder
folder = dataiku.Folder(get_output_names_for_role('folder_with_data')[0])
folder_path = folder.get_path()

# Start sync 
sftp_connector.download_dir(folder_path,sftp_root_path)

print ("Recipe complete")