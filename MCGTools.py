def goget(addr, output): #This function downloads files from HTTP destinations from a list of addresses to locations specified in that list
    import requests
    import cursor
    cursor.hide()
    head = requests.head(addr)
    ftype = head.headers['content-type'] #Gets file type and stores as string
    fsize = int(head.headers['content-length']) #Gets file size (in bytes) and stores as int
    print(f'Downloading from {addr} as {output}')
    print(f'File type: {ftype}  File Size: {fsize}')
    chunk_count = 0 #Counts how many chunks have been downloaded to calculate progress
    with requests.get(addr, stream=True) as r: #Gets in streaming mode to prevent entire file being copied to RAM
        r.raise_for_status() #Outputs debugging data
        with open(output, 'wb') as f: #Opens output file to begin copying data to it
            for chunk in r.iter_content(chunk_size=8192): #Copies data chunk by chunk
                f.write(chunk)
                chunk_count += 1 #Increments chunck count
                prog = int(((chunk_count * 8192) / fsize)*100) #Calculates progress percentage
                print(f'{prog}% Complete.', end = '\r',) #Prints progress percentage
    print("Download complete!")
    cursor.show()
    return output
def makelsdirs(path, dirsls): #This function builds directory trees based upon nested lists
    import os
    for dirs in dirsls: 
        dir_path = os.path.join(path, dirs) #Creates a valid path string for the directory to be created
        os.makedirs(dir_path) #Creates the new directory
        if dirs: #Checks to see if any sub-directories have been specified
            subdirs = dirsls[dirs] #Parses the subdirectories into a new list to be passed into this function again
            makelsdirs(dir_path, subdirs) #Call to this function to make sub-directiories and any of their sub-directories...
def DIRector(path, cFile): #This functions builds directory trees based upon a MCGTools YAML config file
    import yaml
    with open(cFile, 'r') as cOpen:
        config = yaml.safe_load(cOpen)
    dirsls = config['directories'] #Extracts the directory list from the config file
    makelsdirs(path, dirsls) #Passes that list into the directory making function