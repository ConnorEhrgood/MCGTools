from pymongo import MongoClient
from tenacity import *
import os

client = MongoClient(os.environ.get('DB_CONNECT_STRING'))
db = client[os.environ.get('DB_NAME')]

def output(*args, **kwargs): #Function to print data to console ONLY if process is in the foreground
    import os, sys

    if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()): #Checks wheter this process is the process in the foreground of the terminal
        print(*args, **kwargs)


@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_fixed(2))
def goget(addr, output_file): # This function downloads files from HTTP destinations
    import requests

    try:
        head = requests.head(addr)
    except Exception:
        raise Exception('Connection error. Server not found or file may not exist.')
    file_type = head.headers['content-type'] #Gets file type and stores as string
    file_size = int(head.headers['content-length']) #Gets file size (in bytes) and stores as int
    output(f'Downloading from {addr} as {output_file}')
    output(f'File type: {file_type}  File Size: {file_size}')
    
    
    chunk_count = 0 #Counts how many chunks have been downloaded to calculate progress
    current_prog = 0 #Progress value that is printed to terminal
    try:
        with requests.get(addr, stream=True) as r: #Gets in streaming mode to prevent entire file being copied to RAM
            r.raise_for_status() #Outputs debugging data

            with open(output_file, 'wb') as f: #Opens output file to begin copying data to it
                for chunk in r.iter_content(chunk_size=8192): #Copies data chunk by chunk
                    f.write(chunk)
                    chunk_count += 1 #Increments chunck count
                    prog = round(((chunk_count * 8192) / file_size)*100, 1) #Calculates progress percentage
                    if current_prog != prog: #Reduces number of prints to only what is necessary
                        current_prog = prog
                        output(f'{output_file} - Download {current_prog}% complete.', end = '\r') #Prints current progress percentage
        output(f'{output_file} - Download complete!')
    except Exception:
        raise Exception('Download error.')



def megamd5(input_file, make_file=True): # This function generates the MD5 hash of an input file and saves it to a .md5 file with the same name in the same directory as the input file
    import os, hashlib

    file_name = os.path.split(input_file)[1]  #Creates a string of the input filename without the path; i.e. 'file.txt'
    file_base = os.path.splitext(file_name)[0] #Creates a string of the base of the input filename without the extension; i.e. 'file'
    file_path = os.path.split(input_file)[0] #Creates a string of the path to the input filename; i.e. '/home/directory/'
    file_size = os.path.getsize(input_file) #Gets the file size of the input file so progress can be tracked

    if make_file:
        output_file = os.path.join(file_path, f'{file_base}.md5') #Creates the output path for the MD5 hash; i.e. '/home/directory/file.md5'
    else:
        output_file = 'None - Return Only'

    output(f'Generating MD5. Input: {input_file}   Output: {output_file}')

    chunk_count = 0 #Number of chunks processed; Used for progress calculation
    current_prog = 0 #Progress value that is printed to terminal
    with open(input_file, 'rb') as f:
        hash = hashlib.md5()

        while chunk := f.read(16384): #Computes MD5 hash in chunks to avoid loading entire file into ram
            hash.update(chunk)

            chunk_count += 1 #Increments chunck count
            prog = round(((chunk_count * 16384) / file_size)*100, 1) #Calculates progress percentage
            if current_prog != prog: #Reduces number of prints to only what is necessary
                current_prog = prog
                output(f'{current_prog}% Complete.', end = '\r') #Prints current progress percentage

    hexi_hash = hash.hexdigest() #Saves MD5 hash as string

    if make_file:
        with open(output_file, 'w') as o:
            o.write(f'{hexi_hash} {file_name}') #Writes MD5 hash and file name into a text document in a format that md5sum can verify

    output(f'{output_file} - MD5 calculation complete!')
    return(hexi_hash) # Return hash to be use in the function that called this one



def director(path, dirs_list): # This function builds directory trees based upon a dictionary
    import os

    for dirs in dirs_list: 
        dir_path = os.path.join(path, dirs) #Creates a valid path string for the directory to be created
        os.makedirs(dir_path) #Creates the new directory

        if dirs: #Checks to see if any sub-directories have been specified
            subdirs = dirs_list[dirs] #Parses the subdirectories into a new list to be passed into this function again
            director(dir_path, subdirs) #Call to this function to make sub-directiories and any of their sub-directories...



def get_files_list(directory): # This function finds all files in a directory tree and returns them in a list with their full path
    import os

    dir_ls = os.listdir(directory) # Generates a list representing the specified directory
    files_ls = list() # Declares a list to be used for the files found

    for d in dir_ls:

        path = os.path.join(directory, d) 

        if os.path.isdir(path): #Checks to see if current item in list is a directory
            files_ls = files_ls + get_files_list(path) # If it is, call this function in that directory to check for files. Add any files found to the list.
        else:
            files_ls.append(path) # Otherwise, it must be a file, so add it to the list
                
    return files_ls # Return the list of files

@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_fixed(2))
def remmd5(addr): # This function generates the MD5 hash of a remote file on an http server
    import requests, hashlib

    with requests.get(addr, stream=True) as r: #Gets in streaming mode to prevent entire file being copied to RAM
        r.raise_for_status() #Outputs debugging data

        hash = hashlib.md5()

        for chunk in r.iter_content(chunk_size=8192): #Copies data chunk by chunk
            hash.update(chunk)

    hexi_hash = hash.hexdigest() #Saves MD5 hash as string

    return(hexi_hash)



def make_xfer_entry(name, type): #This function adds a transfer entry in the database and returns the entry ID
    from datetime import datetime
    transfer = {
        'name' : name,
        'type' : type,
        'init_time' : datetime.now(),
        'status' : 'Starting...',
    }

    entry = db.transfers.insert_one(transfer).inserted_id
    return entry



def update_xfer_status(xfer_id, status): #This function updates the status of a transfer entry in the database
    db.transfers.update_one({'_id': xfer_id },{ '$set': { 'status': status } })



def add_config_to_entry(xfer_id, config): #This function adds the parsed config to a transfer entry in the database
    db.transfers.update_one({'_id': xfer_id },{ '$set': { 'config': config } })



def add_error_to_entry(xfer_id, file, source, error): #This function adds an error to a transfer entry in the database
    from datetime import datetime
    error_object = {
        'file' : file, 
        'source': source,
        'error' : error,
        'time' : datetime.now()
    }
    db.transfers.update_one({'_id': xfer_id },{ '$push': { 'errors': error_object } })



def add_file_to_entry(xfer_id, file, source, hash): #This function adds an error to a transfer entry in the database
    from datetime import datetime
    name = file.rsplit('/', 1)[-1] 
    file_object = {
        'name' : name, #The Brief name to be displayed in lists in the UI
        'file' : file, #The full name and file location
        'source': source,
        'hash' : hash,
        'time' : datetime.now()
    }
    db.transfers.update_one({'_id': xfer_id },{ '$push': { 'files': file_object } })



### TO-DO - Add error handling and database interaction to GoGetter ###
def gogetter(name, config_file, dir=''): # This function downloads files from HTTP destinations, generated MD5 hashes of those files, and verifies the integrity of those files against the origional
    import os, sys, yaml, requests #Imports necessary libraries
    from threading import Thread

    directory = os.path.join(os.getcwd(), name) #Generates the directory path based upon the current working directory and the name provided

    with open(config_file, 'r') as config_open: #Opens the config file provided
        config = yaml.safe_load(config_open) #Saves the contents of the config file as a list

    files = config['gogetter_files'] #Parses the files to be downloaded into a list
    dir_list = config['gogetter_directories'] #Parses the directories to be created into a nested list

    director(directory, dir_list) #Calls DIRector to create the specified folder tree



    def move(current_addr, output_addr, server):

        output(f'{output_addr} - Thread initialized.')
 
        file_hash = 'file_hash' #Defining the hash strings and setting them to arbitrary, non-equal values
        verify_hash = 'verify_hash'
    
        while(file_hash != verify_hash):

            goget(current_addr, output_addr) #Calls goget to retrieve the specified file

            file_hash = megamd5(output_addr) #Calls megamd5 to generates the MD5 hash for the file

            output(f'{output_addr} - Verifying...')

            verify_hash = remmd5(current_addr) #Generates an MD5 hash of the remote file
            output(f'{output_addr} - File Hash: {file_hash}')
            output(f'{output_addr} - Verify Hash: {verify_hash}')

            if(file_hash == verify_hash): #Checks to make sure the hash of the local file and remote file are the same
                output(f'{output_addr} - File integrity verified. Finishing.')
            else:
                output(f'{output_addr} - File issue detected. Retrying.')

        output(f'{output_addr} - Completed!')




    threads = []
    for file in files:
        current_addr = file['url'] #Parses the URL of the file to be downloaded
        current_dir = file['dir'] #Parses the directory the file is to be downloaded to
        server = current_addr.rsplit('/', 2)[0] #Determines what the address of the server is for API calls
        remote_name = current_addr.rsplit('/', 1)[-1] #Determines the name of the remote file
        local_name = f'{name}_{remote_name}' #Generates the name to be used for the file
        output_addr = os.path.join(name, current_dir, local_name) #Generates the full output path for the file

        t = Thread(target=move, args=(current_addr, output_addr, server, ))
        threads.append(t)
        t.start()


    for t in threads: #Waits for threads to complete
        t.join()

    print('GoGetter Done!')



def ptcopy(name, config_file, dir=''): # This function copies all files in a directory tree to an identical directory tree, appends a given name to the beginning of each file name, verifies the integrity of the data and generates an md5 hash for each file
    import shutil, os, yaml, time

    entry = make_xfer_entry(name, 'PTCopy')

    try:
        with open(config_file, 'r') as config_open: #Opens the config file provided
            config = yaml.safe_load(config_open) #Saves the contents of the config file as a list
    
        if dir: # If a directory was specified...
            directory = dir # ... copy the tree to that directory

        elif 'ptcopy_working_directory' in config: # ... or if a directory was specified in the config file...
            directory = config['ptcopy_working_directory'] # ... copy the tree to that directory

        elif 'working_directory' in config:
            directory = config['working_directory']

        else:
            directory = os.path.join(os.getcwd()) #... Otherwise, generate the directory path based upon the current working directory

        root_dir = 'PTCopy'
        if config['ptcopy_directory_name']: # Checks wheter a directory name was specified...
            root_dir = config['ptcopy_directory_name'] # If so, name the directory that.

        old_dir = config['ptcopy_old_directory']
    
    except Exception:
        update_xfer_status(entry, 'Failed - Config File Error')
        exit(1)

    add_config_to_entry(entry, config) #Adds the config details to the database entry

    new_dir = os.path.join(directory, name, root_dir)

    update_xfer_status(entry, 'Copying Files...')
    try:
        shutil.copytree(old_dir, new_dir) #Coptis the files from the old directory to the new one
    except Exception:
        update_xfer_status(entry, 'Failed - Transfer Error')
        exit(1)

    update_xfer_status(entry, 'Processing...')
    try:
        for new_file in get_files_list(new_dir): #For all files in the new directory...

            old_file = new_file.replace(new_dir, old_dir) #Figure out where the file came from so it can be verified
            output(f'Old File: {old_file} New File: {new_file}')

            old_name = os.path.basename(new_file) #Find the origional name of the file
            path_only = os.path.dirname(new_file) #Find the file path to the new file
            new_name = f'{name}_{old_name}' #Append the transfer name to the file
            new_path = os.path.join(path_only, new_name) #Generate the new full file path

            os.rename(new_file, new_path) #Rename the file
            new_file = new_path
        
            new_file_hash = megamd5(new_file) #Hash the new file
            output(new_file_hash)
            old_file_hash = megamd5(old_file, make_file=False) #Hash the old file without generating the .md5 file; for verificatition 
            output(old_file_hash)

            while new_file_hash != old_file_hash: #If the hashes do not match
                output(f'{new_file} - File issue detected. Retrying.')

                file_base = os.path.splitext(new_file)[0]
                os.remove(f'{file_base}.md5') #Remove the generated MD5 file
                os.remove(new_file) #Remove the copied file

                shutil.copy2(old_file, new_file) #Copy the individual file again

                new_file_hash = megamd5(new_file) #Hash the new copy of the file
                output(new_file_hash)
                old_file_hash = megamd5(old_file, make_file=False)
                output(old_file_hash) #Hash the old file without generating the .md5 file; for verificatition

            output(f'{new_file} - File integrity verified. Finishing.')
    except Exception:
        update_xfer_status(entry, 'Failed - Rename or Verify Error')
        exit(1)

    update_xfer_status(entry, 'Complete!')



def kicopy(name, config_file, dir=''):
    import os, sys, yaml, requests #Imports necessary libraries
    from threading import Thread

    print('An instance of KiCopy has been started.')

    entry = make_xfer_entry(name, 'KiCopy')

    try:
        with open(config_file, 'r') as config_open: #Opens the config file provided
            config = yaml.safe_load(config_open) #Saves the contents of the config file as a list

        if dir: # If a directory was specified...
            root_dir = dir # ... copy the tree to that directory

        elif 'gogetter_working_directory' in config: # ... or if a directory was specified in the config file...
            root_dir = config['gogetter_working_directory'] # ... copy the tree to that directory

        elif 'working_directory' in config:
            root_dir = config['working_directory']

        else:
            root_dir = os.path.join(os.getcwd()) #... Otherwise, generate the directory path based upon the current working directory

        files = config['gogetter_files'] #Parses the files to be downloaded into a list

    except Exception:
        update_xfer_status(entry, 'Failed - Config File Error')
        exit(1)
    
    add_config_to_entry(entry, config) #Adds the config details to the database entry

    directory = os.path.join(root_dir, name) #Generates the full directory path
    output(directory)
    try:
        os.makedirs(directory)
    except FileExistsError:
        if 'ignore_rootdir_error' in config:
            output('Root directory exists, but ignore_rootdir_error is included in the config file. Continuing...')

        else:
            update_xfer_status(entry, 'Failed - Root Directory Already Exists')
            exit(1)
        
        
    except Exception:
        update_xfer_status(entry, 'Failed - Root Directory Error')
        exit(1)

    if 'gogetter_directories' in config:
        try:
            dir_list = config['gogetter_directories'] #Parses the directories to be created into a nested list
            director(directory, dir_list) #Calls DIRector to create the specified folder tree
        except Exception:
            update_xfer_status(entry, 'Failed - Directory Tree Error')
            exit(1)


    def move(server, server_files, name): #The function that each thread will run

        output(f'{server} - Thread initialized.')

        try:
            output(f'{server} - Setting media state to DATA-LAN:')
            output(str(requests.get(f'{server}/config', params = 'action=set&paramid=eParamID_MediaState&value=1', timeout = 10))) #Makes the media state call to the KiPro and prints the response
        except:
            output(f'API Call to {server} failed. Continuing anyway...')

        for file in server_files: 

            current_addr = file['url'] #Parses url form list of files
            current_dir = file['dir'] #Parses directory from list of files
            remote_name = current_addr.rsplit('/', 1)[-1] #Determines the name of the remote file
            file_name = remote_name
            if 'file_name' in file:
                file_name = file['file_name']
            local_name = f'{name}_{file_name}' #Generates the name to be used for the file
            output_addr = os.path.join(directory, current_dir, local_name) #Generates the full output path for the file


            file_hash = 'file_hash' #Defining the hash strings and setting them to arbitrary, non-equal values
            verify_hash = 'verify_hash'
    
            while( file_hash != verify_hash): #If the hashs of the downloaded file and the remote file aren't the same, keep doing this

                try:
                    head = requests.head(current_addr)
                    if head.status_code != 200:
                        raise Exception('Server returned status other than 200.')
                    file_size = int(head.headers['content-length']) #Gets file size (in bytes) and stores as int

                    goget(current_addr, output_addr) #Calls goget to retrieve the specified file
                except Exception:
                    add_error_to_entry(entry, file_name, current_addr, 'Download Error - File Skipped')
                    break

                try:
                    file_hash = megamd5(output_addr) #Calls megamd5 to generates the MD5 hash for the file
                except Exception:
                    add_error_to_entry(entry, file_name, current_addr, 'Hashing Error - Verify Skipped')
                    break

                try:
                    output(f'{output_addr} - Verifying...')

                    local_size = os.path.getsize(output_addr)

                    output(f'Local size: {local_size} Remote size: {file_size}')

                    if(file_size == local_size):
                        verify_hash = remmd5(current_addr) #Generates an MD5 hash of the remote file
                        output(f'{output_addr} - File Hash: {file_hash}')
                        output(f'{output_addr} - Verify Hash: {verify_hash}')

                    if(file_hash == verify_hash): #Checks to make sure the hash of the local file and remote file are the same
                        output(f'{output_addr} - File integrity verified. Finishing.')
                        add_file_to_entry(entry, output_addr, current_addr, file_hash) # If the file copies successfullt and is verified, add it to the files list of the transfer
                    else:
                        os.remove(output_addr)
                        os.remove(f'{os.path.splitext(output_addr)[0]}.md5')
                        output(f'{output_addr} - File issue detected. Retrying.')
                except Exception:
                    add_error_to_entry(entry, file_name, current_addr, 'Verify Error - File Not Verified')
                    break

        try:
            output(f'{server} - Setting media state to RECORD-PLAY:')
            output(str(requests.get(f'{server}/config', params = 'action=set&paramid=eParamID_MediaState&value=0', timeout = 10))) #Makes the media state call to the KiPro and prints the response
        except:
            output(f'API Call to {server} failed. Exiting without changing media state.')

        output(f'{server} - Completed!')

    servers = {}

    for file in files: #Generates a list of files for each server fro the threads to download sequentially. Prevents KiPros from killing connections when multiple requests are made.
        current_addr = file['url'] #Parses the URL of the file to be downloaded
        server = current_addr.rsplit('/', 2)[0] #Determines what the address of the server is
        current_dir = file['dir'] #Parses the directory the file is to be downloaded to

        if server in servers:
            servers[server].append(file) #If the server for this particular file is already in the list of servers, just append the file to the list for that server
        else:
            servers[server] = [file] #If the server for this particular file is not in the list of servers, add the server and append the file to it's list

    threads = []
    update_xfer_status(entry, 'Starting Threads...')
    for server in servers: #Spins up a thread to download the files from each server in parrallel

        server_files = servers[server]

        t = Thread(target=move, args=(server, server_files, name, )) #Defining thread
        threads.append(t) #Adding to the list of threads so it can be joined later
        t.start() #Starts the thread

    update_xfer_status(entry, 'Running...')
    for t in threads: #Wait for all threads to complete
        t.join()

    if not 'errors' in db.transfers.find_one(entry): #Set final status on transfer entry
        update_xfer_status(entry, 'Complete!')
    else:
        update_xfer_status(entry, 'Completed With Errors')

    print('\x1b[6;30;42m' + 'All Done!' + '\x1b[0m')
