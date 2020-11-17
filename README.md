
this is an alternative to the native SFTP downloader|exporter  that supports Sock5 proxies. 


# Installation 

This plugin is meant to be installed as a generic Dataiku DSS plugin. It was  developped and tested on versions (6.0 7.0 and 8.0). 
To install it, you may import the zip archive made of the full content of the plugio into your DSS instance from the interface (Plugin > Add plugin > Upload). 
During the installation of the plugin the installation of the following dependences will be installed in the python environment : 
 * paramiko 
 * pysocks
As per the DSS documentation, the installation of a plugin requires Administration roles. 

# Configuration 

Once the plugin is being installed, It is recommmended to define the different data sources that are to be used by the users called SFTP Services.  
A SFTP Service is defined by "presets" that gathers access and authentications informations to access SFTP sources but also the root location of the work space authorized. During the daily use of the SFTP Plugin , you can also override these informatiions of let the end enter it within a job or so, but Defining a SFTP Service make it avialable immediately and reusable so the user will simply select the source instead of configuring it over and over again. 

To add a new SFTP service, you need to  : 
* go to your plugin settings ( Plugins > Installed > SFTP-Python-Connector > Settings)
* Open the  SFTP Services and click "Add Preset" at the bottom of the page
* Give a name to your service that will be recognized by the end users and click on "Create"

You need to be administrator to perform this configuration 

## Service Settings : 

When configuring a SFTP service , you need to indicate the acces informations or the SFTP server . These sources must be accessible from a network perspective and be technically accessible froom a security perspective. Thus we strongly recommend to test the SSH connection at least  from the server were DSS is being installed user the ssh client of the server  prior to configuring such a Service. 

The basic informations you will be requested are : 
* An optional (but essential) description of the SFTP Service in order to inform of the purpose or use for this Service
* the "hostname" which is the fully qualified domain name or the IP address of your SFTP server. You should NOT add the add the protocal in the field but simply the domain name like "my.server.name" or "123.45.67.89". [Mandatory]
* the access port of your SFTP Server [Mandatory]
Secondly you may choose the "SSH authentication" method to your SFTP Server. 
* the "password option " will require a classic username/password pair of informations
* the "Private Key" option requires that you have a Private key on the local machine for which the publy key is put on the authorized Key list of your SFTP server. You will be requested your "username"  and the path to your private key via the field "ssh private key"

Optionnally you can define a proxy server in case the access to your SFTP Server depends on it. 
you can chose between HTTP and Sock5 proxies and you will be requested a hostname and port for the proxy via the fields "Proxy hostname" and "Proxy port" fields. 
If your proxy requires authentication  you can set the "Proxy user" and "Proxy password" to define it. 
If your proxy doesn't require authentication, you can simply leave these field empty, as the authencitation will be ignored if "Proxy user" is not defined.

As a reminder, all the password fields are being encrypted by DSS using AES 256 key. (or a key with a custom lenght  acccording to the configuration of your instance. See the reference documentation for more details)


## Authorization  

You can also set or restrict the access or the use of this preset by defining : 
* the owner of this SFTP Service. 
* a list of groups that can use your SFTP Service via the authorization "Can use preset"

# Usage 

This plugin contains 3 main features : 
* A recipe that performs a "Download from SFTP" directories into a local Dataiku Folder
* A recipe that performs an "Exprot to SFTP" directory from the content of a Dataiku Folder
* An exporter to sftp that allows to upload the content of a Dataiku Dataset


## Recipe : Download from SFTP 

This plugin recipe allows any user to download recursively the content of a Directory in your SFTP server and store it in a local Dataiku folder. This dataiku folder will be created as an output of the dataset 


The recipes is accessible from the workflow by click on " Recipes (at the top of the workflow) > SFTP Python Connector > Download from SFTP  ".

You will be requested to create a Folder as an output for the recipe, This folder MUST be created from a local filesystem connection as it is the only source supported. 

Once your recipe is created you need to select : 
* The SFTP service that you wish to use (or completely define the informations of your SFTP server based on the same filead as the SFTP service)
* the path of the directory you wish to download


After the first execution that will fully download the entire SFTP directory , the files will be refreshed in a smart way according to the following rules : 
* any new remote element  will be downloaded
* if the source file is updated on the SFTP , it will be download 
* if the remote and local files are the same (size and creation date) they will be ignored. 

Beware that the folder is not emptied at each execution and will be instead keeping the content of the previous dowload  unless there a file to update. if you wish to clear the the folder content at each execution you need to do it manually via the action clear or to use a scenario step "Clear". 

## Recipe : Exprot to SFTP 

This plugin recipe pushes the content of a DSS local Folder to a SFTP server the selected directory, it will also create a list of the files downloaded and store it into an output dataset

As for the Dowload recipe, this one is accessible from the workflow, on " Recipes (at the top of the workflow) > SFTP Python Connector > Exprot to SFTP ".

You will be requested to select the source folder that contains the files you wish to upload as an output and a name for the dataset that will containt the list of the files uploaded successfully. 
Once your recipe is created you need to select : 
* The SFTP service that you wish to use (or completely define the informations of your SFTP server based on the same filead as the SFTP service)
* the path of the directory you wish to push your files into


After the first execution, the files will be refreshed in a smart way according to the following rules : 
* any new element in the local Dataiku Folder will be uploaded
* if the source file is updated on the Dataiku folder , it will be uploaded and override the previous file 
* if the remote and local files are the same (size and creation date) they will be ignored. 

## Custom SFTP exporter 

The exporter is accessible : 
* either interactively from the dataset  by clicking on action > export  > other (Plugin) > Export to SFTP 
* or via the export recipe in the from the tab "Other export"




