def output(data, end = '\n'): #Function to print data to console ONLY if process is in the foreground
    import os, sys

    if os.getpgrp() == os.tcgetpgrp(sys.stdout.fileno()): #Checks wheter this process is the process in the foreground of the terminal
        print(data, end = end)


def goget(addr, output_file): #This function downloads files from HTTP destinations from a list of addresses to locations specified in that list
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
                    output(f'{current_prog}% Complete.', end = '\r') #Prints current progress percentage
    output("Download complete!")


def megamd5(input_file): #This function generates the MD5 hash of an input file ans saves it to a .md5 file with the same name in the same directory as the input file
    import os, hashlib

    file_name = os.path.split(input_file)[1]  #Creates a string of the input filename without the path; i.e. 'file.txt'
    file_base = os.path.splitext(file_name)[0] #Creates a string of the base of the input filename without the extension; i.e. 'file'
    file_path = os.path.split(input_file)[0] #Creates a string of the path to the input filename; i.e. '/home/directory/'
    output_path = os.path.join(file_path, f'{file_base}.md5') #Creates the output path for the MD5 hash; i.e. '/home/directory/file.md5'
    file_size = os.path.getsize(input_file) #Gets the file size of the input file so progress can be tracked

    output(f'Generating MD5. Input: {input_file}   Output: {output_path}')

    chunk_count = 0 #Number of chunks processed; Used for progress calculation
    current_prog = 0 #Progress value that is printed to terminal
    with open(input_file, 'rb') as f:
        file_md5 = hashlib.md5()

        while chunk := f.read(16384): #Computes MD5 hash in chunks to avoid loading entire file into ram
            file_md5.update(chunk)

            chunk_count += 1 #Increments chunck count
            prog = round(((chunk_count * 16384) / file_size)*100, 1) #Calculates progress percentage
            if current_prog != prog: #Reduces number of prints to only what is necessary
                current_prog = prog
                output(f'{current_prog}% Complete.', end = '\r') #Prints current progress percentage

    hexi_sum = file_md5.hexdigest() #Saves MD5 hash as string

    with open(output_path, 'w') as o:
        o.write(f'{hexi_sum} {file_name}') #Writes MD5 hash and file name into a text document in a format that md5sum can verify

    output('MD5 calculation complete!')

def director(path, dirs_list): #This function builds directory trees based upon nested lists
    import os

    for dirs in dirs_list: 
        dir_path = os.path.join(path, dirs) #Creates a valid path string for the directory to be created
        os.makedirs(dir_path) #Creates the new directory

        if dirs: #Checks to see if any sub-directories have been specified
            subdirs = dirs_list[dirs] #Parses the subdirectories into a new list to be passed into this function again
            director(dir_path, subdirs) #Call to this function to make sub-directiories and any of their sub-directories...