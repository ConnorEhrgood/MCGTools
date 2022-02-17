def goget(addr, output): #This function downloads files from HTTP destinations from a list of addresses to locations specified in that list
    import requests
    import cursor

    cursor.hide()

    head = requests.head(addr)
    file_type = head.headers['content-type'] #Gets file type and stores as string
    file_size = int(head.headers['content-length']) #Gets file size (in bytes) and stores as int
    print(f'Downloading from {addr} as {output}')
    print(f'File type: {file_type}  File Size: {file_size}')

    chunk_count = 0 #Counts how many chunks have been downloaded to calculate progress
    with requests.get(addr, stream=True) as r: #Gets in streaming mode to prevent entire file being copied to RAM
        r.raise_for_status() #Outputs debugging data

        with open(output, 'wb') as f: #Opens output file to begin copying data to it
            for chunk in r.iter_content(chunk_size=8192): #Copies data chunk by chunk
                f.write(chunk)
                chunk_count += 1 #Increments chunck count
                prog = int(((chunk_count * 8192) / file_size)*100) #Calculates progress percentage
                print(f'{prog}% Complete.', end = '\r',) #Prints progress percentage

    print("Download complete!")
    cursor.show()



def makelsdirs(path, dirsls): #This function builds directory trees based upon nested lists
    import os

    for dirs in dirsls: 
        dir_path = os.path.join(path, dirs) #Creates a valid path string for the directory to be created
        os.makedirs(dir_path) #Creates the new directory

        if dirs: #Checks to see if any sub-directories have been specified
            subdirs = dirsls[dirs] #Parses the subdirectories into a new list to be passed into this function again
            makelsdirs(dir_path, subdirs) #Call to this function to make sub-directiories and any of their sub-directories...



def megamd5(file): #This function generates the MD5 hash of an input file ans saves it to a .md5 file with the same name in the same directory as the input file
    import os
    import hashlib

    file_name = os.path.split(file)[1]  #Creates a string of the input filename without the path; i.e. 'file.txt'
    file_base = os.path.splitext(file_name)[0] #Creates a string of the base of the input filename without the extension; i.e. 'file'
    file_path = os.path.split(file)[0] #Creates a string of the path to the input filename; i.e. '/home/directory/'
    output_path = os.path.join(file_path, f'{file_base}.md5') #Creates the output path for the MD5 hash; i.e. '/home/directory/file.md5'

    with open(file, 'rb') as f:
        file_md5 = hashlib.md5()

        while chunk := f.read(16384): #Computes MD5 hash in chunks to avoid loading entire file into ram
            file_md5.update(chunk)

    hexi_sum = file_md5.hexdigest() #Saves MD5 hash as string

    with open(output_path, 'w') as o:
        o.write(f'{hexi_sum} {file_name}') #Writes MD5 hash and file name into a text document in a format that md5sum can verify



def DIRector(path, cFile): #This functions builds directory trees based upon a MCGTools YAML config file
    import yaml

    with open(cFile, 'r') as cOpen:
        config = yaml.safe_load(cOpen) #Saves the contents of the config file as a list

    dirsls = config['directories'] #Extracts the directory list from the config file
    makelsdirs(path, dirsls) #Passes that list into the directory making function