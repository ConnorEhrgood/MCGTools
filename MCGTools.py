def output(*args, **kwargs): #Function to print data to console ONLY if process is in the foreground
    import os, sys

    if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()): #Checks wheter this process is the process in the foreground of the terminal
        print(*args, **kwargs)



def goget(addr, output_file): # This function downloads files from HTTP destinations
    import requests

    head = requests.head(addr)
    file_type = head.headers['content-type'] #Gets file type and stores as string
    file_size = int(head.headers['content-length']) #Gets file size (in bytes) and stores as int
    output(f'Downloading from {addr} as {output_file}')
    output(f'File type: {file_type}  File Size: {file_size}')
    
    
    chunk_count = 0 #Counts how many chunks have been downloaded to calculate progress
    current_prog = 0 #Progress value that is printed to terminal
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



def remmd5(addr): # This function generates the MD5 hash of a remote file on an http server
    import requests, hashlib

    with requests.get(addr, stream=True) as r: #Gets in streaming mode to prevent entire file being copied to RAM
        r.raise_for_status() #Outputs debugging data

        hash = hashlib.md5()

        for chunk in r.iter_content(chunk_size=8192): #Copies data chunk by chunk
            hash.update(chunk)

    hexi_hash = hash.hexdigest() #Saves MD5 hash as string

    return(hexi_hash)



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

    with open(config_file, 'r') as config_open: #Opens the config file provided
        config = yaml.safe_load(config_open) #Saves the contents of the config file as a list

    if dir: # If a directory was specified...
        directory = dir # ... copy the tree to that directory

    elif config['ptcopy_working_directory']: # ... or if a directory was specified in the config file...
        directory = config['ptcopy_working_directory'] # ... copy the tree to that directory

    elif config['working_directory']:
        directory = config['working_directory']

    else:
        directory = os.path.join(os.getcwd()) #... Otherwise, generate the directory path based upon the current working directory

    root_dir = 'PTCopy'
    if config['ptcopy_directory_name']: # Checks wheter a directory name was specified...
        root_dir = config['ptcopy_directory_name'] # If so, name the directory that.

    old_dir = config['ptcopy_old_directory']
    new_dir = os.path.join(directory, name, root_dir)

    shutil.copytree(old_dir, new_dir)

    output('Waiting for corruption (for testing)...')
    time.sleep(20)

    for new_file in get_files_list(new_dir):

        old_file = new_file.replace(new_dir, old_dir)
        output(f'Old File: {old_file} New File: {new_file}')

        old_name = os.path.basename(new_file)
        path_only = os.path.dirname(new_file)
        new_name = f'{name}_{old_name}'
        new_path = os.path.join(path_only, new_name)

        os.rename(new_file, new_path)

        new_file = new_path
        
        new_file_hash = megamd5(new_file)
        output(new_file_hash)
        old_file_hash = megamd5(old_file, make_file=False)
        output(old_file_hash)

        while new_file_hash != old_file_hash:
            output(f'{new_file} - File issue detected. Retrying.')

            file_base = os.path.splitext(new_file)[0]
            os.remove(f'{file_base}.md5')
            os.remove(new_file)

            shutil.copy2(old_file, new_file)

            new_file_hash = megamd5(new_file)
            output(new_file_hash)
            old_file_hash = megamd5(old_file, make_file=False)
            output(old_file_hash)

        output(f'{new_file} - File integrity verified. Finishing.')



def kicopy(name, config_file, dir=''):
    import os, sys, yaml, requests #Imports necessary libraries
    from threading import Thread

    print('An instance of KiCopy has been started.')


    with open(config_file, 'r') as config_open: #Opens the config file provided
        config = yaml.safe_load(config_open) #Saves the contents of the config file as a list

    if dir: # If a directory was specified...
        root_dir = dir # ... copy the tree to that directory

    elif config['gogetter_working_directory']: # ... or if a directory was specified in the config file...
        root_dir = config['gogetter_working_directory'] # ... copy the tree to that directory

    elif config['working_directory']:
        root_dir = config['working_directory']

    else:
        root_dir = os.path.join(os.getcwd()) #... Otherwise, generate the directory path based upon the current working directory

    directory = os.path.join(root_dir, name) #Generates the full directory path
    output(directory)

    files = config['gogetter_files'] #Parses the files to be downloaded into a list
    dir_list = config['gogetter_directories'] #Parses the directories to be created into a nested list

    director(directory, dir_list) #Calls DIRector to create the specified folder tree



    def move(server, server_files, name): #The function that each thread will run

        output(f'{server} - Thread initialized.')

        output(f'{server} - Setting media state to DATA-LAN:')
        output(str(requests.get(f'{server}/config', params = 'action=set&paramid=eParamID_MediaState&value=1', timeout = 10))) #Makes the media state call to the KiPro and prints the response

        for file in server_files: 

            current_addr = file['url'] #Parses url form list of files
            current_dir = file['dir'] #Parses directory from list of files
            remote_name = current_addr.rsplit('/', 1)[-1] #Determines the name of the remote file
            local_name = f'{name}_{remote_name}' #Generates the name to be used for the file
            output_addr = os.path.join(directory, current_dir, local_name) #Generates the full output path for the file


            file_hash = 'file_hash' #Defining the hash strings and setting them to arbitrary, non-equal values
            verify_hash = 'verify_hash'
    
            while(file_hash != verify_hash): #If the hashs of the downloaded file and the remote file aren't the same, keep doing this

                goget(current_addr, output_addr) #Calls goget to retrieve the specified file

                file_hash = megamd5(output_addr) #Calls megamd5 to generates the MD5 hash for the file

                output(f'{output_addr} - Verifying...')

                verify_hash = remmd5(current_addr) #Generates an MD5 hash of the remote file
                output(f'{output_addr} - File Hash: {file_hash}')
                output(f'{output_addr} - Verify Hash: {verify_hash}')

                if(file_hash == verify_hash): #Checks to make sure the hash of the local file and remote file are the same
                    output(f'{output_addr} - File integrity verified. Finishing.')
                else:
                    os.remove(output_addr)
                    os.remove(os.path.join(os.path.splitext(output_addr)[0], '.md5'))
                    output(f'{output_addr} - File issue detected. Retrying.')

        output(f'{server} - Setting media state to RECORD-PLAY:')
        output(str(requests.get(f'{server}/config', params = 'action=set&paramid=eParamID_MediaState&value=0', timeout = 10))) #Makes the media state call to the KiPro and prints the response

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

    for server in servers: #Spins up a thread to download the files from each server in parrallel

        server_files = servers[server]

        t = Thread(target=move, args=(server, server_files, name, )) #Defining thread
        threads.append(t) #Adding to the list of threads so it can be joined later
        t.start() #Starts the thread

    for t in threads: #Wait for all threads to complete
        t.join()

    print('\x1b[6;30;42m' + 'All Done!' + '\x1b[0m')