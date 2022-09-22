def output(*args, **kwargs): #Function to print data to console ONLY if process is in the foreground
    import os, sys

    if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()): #Checks wheter this process is the process in the foreground of the terminal
        print(*args, **kwargs)



def goget(addr, output_file): #This function downloads files from HTTP destinations
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



def megamd5(input_file, make_file=True): #This function generates the MD5 hash of an input file and saves it to a .md5 file with the same name in the same directory as the input file
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
    return(hexi_hash)



def director(path, dirs_list): #This function builds directory trees based upon nested lists
    import os

    for dirs in dirs_list: 
        dir_path = os.path.join(path, dirs) #Creates a valid path string for the directory to be created
        os.makedirs(dir_path) #Creates the new directory

        if dirs: #Checks to see if any sub-directories have been specified
            subdirs = dirs_list[dirs] #Parses the subdirectories into a new list to be passed into this function again
            director(dir_path, subdirs) #Call to this function to make sub-directiories and any of their sub-directories...



def remmd5(addr): #This function generates the MD5 hash of a remote file on an http server
    import requests, hashlib

    with requests.get(addr, stream=True) as r: #Gets in streaming mode to prevent entire file being copied to RAM
        r.raise_for_status() #Outputs debugging data

        hash = hashlib.md5()

        for chunk in r.iter_content(chunk_size=8192): #Copies data chunk by chunk
            hash.update(chunk)

    hexi_hash = hash.hexdigest() #Saves MD5 hash as string

    return(hexi_hash)



def gogetter(name, config_file): #This function downloads files from HTTP destinations, generated MD5 hashes of those files, and verifies the integrity of those files against the origional
    import os, sys, yaml, requests #Imports necessary libraries
    import MCGTools as mt #Imports MCGTools (as mt) so we can use it's functions (goget, DIRector, megamd5, output)
    from threading import Thread

    output = mt.output #Lets us call output without "mt." at the beginning

    directory = os.path.join(os.getcwd(), name) #Generates the directory path based upon the current working directory and the name provided

    with open(config_file, 'r') as config_open: #Opens the config file provided
        config = yaml.safe_load(config_open) #Saves the contents of the config file as a list

    files = config['files'] #Parses the files to be downloaded into a list
    dir_list = config['directories'] #Parses the directories to be created into a nested list

    mt.director(directory, dir_list) #Calls DIRector to create the specified folder tree



    def move(current_addr, output_addr, server):

        output(f'{output_addr} - Thread initialized.')
 
        file_hash = 'file_hash' #Defining the hash strings and setting them to arbitrary, non-equal values
        verify_hash = 'verify_hash'
    
        while(file_hash != verify_hash):

            mt.goget(current_addr, output_addr) #Calls goget to retrieve the specified file

            file_hash = mt.megamd5(output_addr) #Calls megamd5 to generates the MD5 hash for the file

            output(f'{output_addr} - Verifying...')

            verify_hash = mt.remmd5(current_addr) #Generates an MD5 hash of the remote file
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

