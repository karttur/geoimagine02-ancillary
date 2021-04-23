'''
Created on 11 Mar 2021

@author: thomasgumbricht
'''

from os import path, makedirs, walk

from sys import exit

from geoimagine.ktgdal import MakeMosaic

class MosaicAncillary():
    ''' class for downloading ancillary data'''
       
    def __init__(self, pp):
        '''
        '''
           
        self.process = pp.process  
        
        self.verbose = self.process.verbose
        
        dstExists= self._SetDstFPN(pp)
        
        if dstExists:
            
            return
    
        if self.process.parameters.mosaiccode.lower() == 'subdirfiles':
            
            self._MosaicSubDirFiles()
            
        else:
            
            exitstr = 'EXITING  - unrecognized mosaiccode in ancillary.mosaic.mosaciancillary'
            
            exit(exitstr)
            
            
    def _SetDstFPN(self,pp):
        '''
        '''
        
        for locus in pp.dstLayerD:
                                
                for datum in pp.dstLayerD[locus]:
                    
                    for comp in pp.dstLayerD[locus][datum]:
                        
                        self.dstFPN = pp.dstLayerD[locus][datum][comp].FPN
                                                            
                        return pp.dstLayerD[locus][datum][comp]._Exists()
                                                                   

    def _MosaicSubDirFiles(self):
        '''
        '''
        
        srcRootFP = path.join('/volumes',self.process.srcpath.volume,self.process.parameters.datadir)
                
                            
        tileL = []
        
        for thepath, subdirs, files in walk(srcRootFP):
            
            for f in files:
                
                if f.endswith(self.process.srcpath.hdr):
                    
                    tileL.append(path.join(thepath, f))
                
        if len(tileL) == 0:
            
            exitstr = 'No tiles found for mosaicking in msoaciAncillary'
            
            exit (exitstr)
                        
        vrtFPN = MakeMosaic(tileL, self.dstFPN)
        
        infostr = '        Ancillary Mosaic created:\n            %s' %(vrtFPN)
        
        print (infostr)
        
        
