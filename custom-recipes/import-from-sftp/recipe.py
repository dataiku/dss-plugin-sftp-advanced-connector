# -*- coding: utf-8 -*-
import dataiku
from dataiku.customrecipe import *
import json
from sftp_client import SftpConnector
import shutil

print ("Custom Recipe being")


# get recipe config
sftp_service = get_recipe_config()['sftpService']
sftp_root_path = get_recipe_config()['sftp_root_path']# we keep the name for migration purpose
bufsize = get_recipe_config()['bufsize']

# Load connector from  python-lib
sftp_connector = SftpConnector(sftp_service)

# get the full location of local folder
source_folder = dataiku.Folder(get_input_names_for_role('sftp_source_folder')[0])

if source_folder.get_info().get("type") != "fsprovider_sftp-python_sftp-python_sftp-fs-provider":
    raise TypeError(" This recipe expects a sftp-python folder as an input")

# get the full location of dest_folder
dest_folder = dataiku.Folder(get_output_names_for_role('folder_with_data')[0])


# Helpers
def download_directory(directory):
    details = source_folder.get_path_details(directory)
    print("start downloading directory: {}".format(details.get("fullPath")))
    for child in details.get("children"):
        if (child.get("directory")):
            download_directory(child.get("fullPath"))
        else: 
            print("start downloading file: {}".format(child.get("fullPath")))
            with source_folder.get_download_stream(child.get("fullPath")) as source_file:
                with dest_folder.get_writer(child.get("fullPath").replace(sftp_root_path,"/",1)) as dest_file:
                    shutil.copyfileobj(source_file, dest_file,bufsize)
            print("succeded downloading file: {}".format(child.get("fullPath")))
    print("Finished downloading directory: {}".format(details.get("fullPath")))
    return

# MAIN PROCESSING
download_directory(sftp_root_path)


print ("Recipe complete")