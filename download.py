'''
Created on 11 Mar 2021

@author: thomasgumbricht
'''

from os import path, makedirs

from sys import exit

import requests 


class DownloadAncillary():
    ''' class for downloading ancillary data'''
       
    def __init__(self, pp):
        '''
        '''
           
        self.process = pp.process  
        
        self.verbose = self.process.verbose
        
    
        if self.process.parameters.downloadcode.lower() == 'filelist':
            
            self._DownloadFileList()
            
        else:
            
            BALLE

    def _DownloadFileList(self):
        '''
        '''
        
        listFPN = path.join('/Volumes',self.process.srcpath.volume,self.process.parameters.path)
        
        if not path.isfile(listFPN):
            
            exitstr = ('Exiting from DownloadAncillary, file not found:\n    %s') %(listFPN)
            
            exit(exitstr)
        
        with open(listFPN) as f:
            
            content = f.readlines()
            
        #  remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        
        for line in content:
            
            if line[0:4] == 'http':
                
                # split line at blanks
                
                url = line.split()[0]
                
                fn = path.split(url)[1]
                
                localFP = path.join('/Volumes',self.process.dstpath.volume,self.process.parameters.datadir)
                
                if not path.exists(localFP):
                    
                    makedirs(localFP)
                
                localFPN = path.join(localFP,fn)
                                
                if not path.exists(localFPN):
                    
                    # Download the file
                
                    print ('downloading ', url, '\nto',  localFPN)
                    
                    self._DownloadUrl(url, localFPN)

    def _DownloadUrl(self, url, save_path, chunk_size=128):
        '''
        '''
        r = requests.get(url, stream=True)
        
        with open(save_path, 'wb') as fd:
            
            for chunk in r.iter_content(chunk_size=chunk_size):
                
                fd.write(chunk)