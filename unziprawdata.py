'''
Created on 23 Mar 2021

@author: thomasgumbricht
'''

from sys import exit
import os

from geoimagine.gis import kt_gis as ktgis

from geoimagine.zipper import UnZip


def CsvFileGetPath1(listfilepath):
          
    with open(listfilepath) as f:
        
        content = f.readlines()

    zipList = [x.strip() for x in content] 
    
    zipList = [os.path.split(z)[1] for z in zipList]
    
    return zipList

def UnZipRawData(volume,params):
    '''
    '''
    rootdir = params.rootdir
    
    listfilepath = params.path
    
    srcsubdir = params.srcsubdir
    
    dstsubdir = params.dstsubdir
    
    pattern = params.pattern

    patternreplace = params.pattern
    
    zipreplace = params.zipreplace
    
    getlist = params.getlist
    
    topdir = os.path.join('/Volumes',volume,rootdir)
    
    dstFP = os.path.join(topdir,dstsubdir)
    
    if not os.path.exists(dstFP):
        
        os.makedirs(dstFP)
        
    if getlist == 'csvfile-getpath1':
        
        zipList = CsvFileGetPath1(listfilepath)
        
    else:
        
        MOREALTERANTIVES
    

    
    for zipFN in zipList:
        
        if srcsubdir == '':
            
            zipFPN = os.path.join(topdir,zipFN)
            
        else:
            
            zipFPN = os.path.join(topdir,srcsubdir,zipFN)
        
        dstFN = zipFN.replace('.zip',zipreplace)
        
        if  patternreplace != 'pattern':
            
            dstFN = dstFN.replace(pattern,patternreplace)

        dstFPN = os.path.join(topdir,dstsubdir,dstFN)
        
        if os.path.exists(zipFPN) and not os.path.exists(dstFPN):
            
            print ('unzip',zipFPN,dstFPN)
            
            UnZip(zipFPN, dstFP, dstFN, pattern)