# -*- coding: utf-8 -*-
import dataiku
from dataiku.customrecipe import *
from dataikuapi.dssclient import DSSClient
import pandas as pd
import json
from sftp_client import SftpConnector

print ("Custom Recipe being")

# get recipe config
sftp_service = get_recipe_config()['sftpService']
sftp_root_path = get_recipe_config()['sftp_root_path']

# load connector
sftp_connector = SftpConnector(sftp_service)

# get the full location of local folder
source_folder = dataiku.Folder(get_input_names_for_role('folder_with_data')[0])
source_folder_path = source_folder.get_path()


# Start sync 
list_of_files_updated = sftp_connector.upload_dir(source_folder_path,sftp_root_path)


#Save the 
out_df = pd.DataFrame()
out_df['Files Updated'] = list_of_files_updated

output_dataset = dataiku.Dataset(get_output_names_for_role('export_details')[0])
output_dataset.write_with_schema(out_df)