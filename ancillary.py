'''
Created on 22 Jan 2021

@author: thomasgumbricht
'''

# Standard library imports

import os

import subprocess

from sys import exit

from shutil import copyfile, copyfileobj

# Third party imports

# Package application imports

from params import Composition, RegionLayer, RasterLayer

from ancillary import ancillary_import

import support.karttur_dt as mj_dt 

from gis import GetVectorProjection, GetRasterMetaData, MjProj

class AncilComposition(Composition): 
    def __init__(self,compD):
        """The constructor requires a dict {datadir, datafile, compyright,title,accessdate,theme,subtheme,label,version,
        dataset,product,datapath,metapath,dataurl,metaurl}.""" 
        
        for key, value in compD.items():
        
            if not hasattr(self, key):
            
                setattr(self, key, value) 

    def SetDataFiletype(self,filetype):
        '''
        '''
        self.datafiletype = filetype
   
    def SetPath(self,mainpath):
        '''
        '''
        self.FP = os.path.join(mainpath,self.datadir)
        
class AncillaryLayer(RegionLayer):
    'Common base class for Ancillary spatial data of different formats'
    
    def __init__(self, comp, rawComp, region, acqdate, process):
        '''
        '''
        
        self.comp = comp
        
        self.layertype = 'ancillary'
        
        self.comp = comp
        
        self.rawComp = rawComp   
        
        self.acqdate = acqdate
        
        self.ancilid = '%(p)s.%(d)s' %{'p':process.dsid,'d':rawComp.datalayer}  

        if len(rawComp.accessdate) >= 4:
            
            self.accessdate = mj_dt.yyyymmddDate(rawComp.accessdate) 
            
        else:
            
            self.accessdate = mj_dt.Today()
            
        self.createdate = mj_dt.Today()
        
        self.FPN = False
        
        if self.comp.hdr == 'ers':
        
            FN = '%(f)s.%(d)s.%(e)s' %{'f':self.rawComp.datafile,'d':self.comp.dat,'e':self.comp.hdr}
        
        else:
        
            if len(self.comp.hdr) > 0:
            
                FN = '%(f)s.%(e)s' %{'f':self.rawComp.datafile,'e':self.comp.hdr}
            
            elif len(self.dat) > 0:
            
                FN = '%(f)s.%(e)s' %{'f':self.rawComp.datafile,'e':self.comp.dat}
            
            elif len(self.comp.hdr) == 0 and len(self.comp.dat) == 0:
            
                #The data is in a folder, e.g. ArcVew raster format
                FN = self.datafile
            
            else:
            
                print (self.datafile,self.dat,self.hdr)
                
                exit('FN error in ancillary')
        
        #For some reason os.path.join does not work here
        FP = '%s/%s' %(self.comp.mainpath,self.rawComp.datadir)
        #FP = os.path.join(ancilC.mainpath,self.datadir)  
        
        self.FPN = os.path.join(FP,FN)
                
        #add the path except for volume and mai folder + to add to db
        dbFP = os.path.join(self.rawComp.datadir,FN)
        
        dbFP = '../%(d)s' %{'d':dbFP}
        
        self.dbFP = dbFP
        
        if self.comp.hdr in ['zip']:
        
            self.zip = 'zip'
        
        elif self.comp.hdr in ['tar.gz','tar']:
        
            self.zip = 'tar.gz'
        
        else:
        
            self.zip = False 
            
    def _UnZip(self):
        '''
        '''
        
        import zipfile
        
        zipFP,zipFN = os.path.split(self.FPN)
        
        tempFP = os.path.join(zipFP,'ziptmp')
        
        self.tempFP = tempFP
        
        if not os.path.isdir(tempFP):
        
            os.makedirs(tempFP)
        
        zipF = zipfile.ZipFile(self.FPN, "r")
        
        self.FPN = False
        
        #compstr is the filetype to look for in the zipfile
        compstr = '.%(e)s' %{'e':self.comp.dat}
        
        for fname in zipF.namelist():
        
            fname = os.path.basename(fname) 
            
            # skip directories
            if not fname:
            
                continue
            
            #get the fname components
            
            stem,ext = os.path.splitext(fname)
            
            fnameout = '%(s)s%(e)s' %{'s':stem, 'e':ext.lower()}
            
            #check if thsi file is of the data type expected
            
            if ext.lower() == compstr:
            
                if self.FPN: 
                
                    exitstr = 'EXITING - ancullary zip archice %(s)s contains multiple data files, you must unzip and give data filenames' %{'s':zipFN}
                    
                    exit(exitstr)
                
                else:
                
                    #Change hdr type
                    
                    self.comp.hdr = self.comp.dat
                    
                    self.FPN = os.path.join(tempFP,fnameout)
            
            # copy file (taken from zipfile's extract)
            
            source = zipF.open(fname)
            
            target = file(os.path.join(tempFP, fnameout), "wb")
            
            with source, target:
            
                copyfileobj(source, target)
                
                if self.verbose:
                
                    print ('shutil.copyfileobj',source, target)
        
        if not self.FPN:
        
            exit('Exiting, no supported file type found in the zip file')
        
        if not os.path.isfile(self.FPN):
        
            exit('Something wrong with the unzipping of ancillary data')
      
    def _UnTar(self):
        import tarfile
        if self.comp.hdr == 'tar.gz':
            tarFPN = os.path.splitext(self.FPN)[0]
            tarFP,tarFN = os.path.split(tarFPN)
            if not os.path.isfile(tarFPN):
                cmd = 'cd %(d)s; gunzip -dk %(s)s' %{'d':tarFP, 's':os.path.split(self.FPN)[1]}
                os.system(cmd)
        else:
            tarFPN = self.FPN   
        tempFP = os.path.join(tarFP,'tartmp')
        self.tempFP = tempFP
        if not os.path.isdir(tempFP):
            os.makedirs(tempFP) 
        
        #compstr is the filetype to look for in the zipfile
        compstr = '.%(e)s' %{'e':self.comp.dat}
        
        tarF = tarfile.TarFile(tarFPN, "r")
        self.FPN = False
        for fname in tarF.getnames():
            fname = os.path.basename(fname) 
            # skip directories
            if not fname:
                continue
        
            #get the fname components
            ext = os.path.splitext(fname)[1]
            
            #check if this file is of the data type expected
            if ext.lower() == compstr:
            
                if self.FPN: 
                
                    exitstr = 'EXITING - ancillary zip archice %(s)s contains multiple data files, you must unzip and give data filenames' %{'s':tarFN}
                    
                    exit(exitstr)
                
                else:
                
                    #Change hdr type
                    self.comp.hdr = self.comp.dat
                    
                    self.FPN = os.path.join(tempFP,fname)
            
            tarF.extract(fname, tempFP)
        
        if self.zip == 'tar.gz':
        
            #remove the tar file
            os.remove(tarFPN)
        
        if not os.path.isfile(self.FPN):
        
            exit('Someting wrong with the unzipping of ancillary data')
            
class ProcessAncillary:
    'class for addint ancillary data'   
    def __init__(self, pp,session):
        '''
        '''
        
        self.session = session
                
        self.pp = pp  
        
        self.verbose = self.pp.process.verbose 
        
        self.session._SetVerbosity(self.verbose)       
        
        # Direct to subprocess
        if self.pp.process.processid == 'OrganizeAncillary':
            
            self._OrganizeAncillary()
        
        elif self.process.proc.processid == 'anciltxttodb':
        
            self._AncilTxtToDb(session)
        
        else:
        
            print (self.process.proc.processid)

            exit('Ancillary process not recognized in ancillary')
        
                   
    def _OrganizeAncillary(self):
        '''
        '''

        self.dsid  = '%(i)s.%(c)s.%(v)s.%(r)s' %{'i':self.pp.process.parameters.orgid,'c':self.pp.process.parameters.dsname,'v':self.pp.process.parameters.dsversion,'r':self.pp.process.parameters.regionid}
        
        self.dsplotid = '%(i)s.%(c)s.%(r)s' %{'i':self.pp.process.parameters.orgid,'c':self.pp.process.parameters.dsname,'r':self.pp.process.parameters.regionid}
        
        
        # Check the srcraw paramters
        self.pp._AssembleSrcRaw(self.session)
        
        #check that the region exists as default, otherwise it must first be created
        rec = self.session._SelectDefaultRegion(self.pp.process.parameters.regionid)

        if rec == None:
        
            exitstr ='Organizing ancillary or specimen data requires an existing region: %s does not exist' %(self.pp.process.parameters.regionid)
            
            exit(exitstr)

        if len(self.pp.dstLayerD) == 0:
            
            exitstr = 'EXITING, no locus defined in Ancillary.OrganizeAncillary'
            
            exit(exitstr)
        
        for locus in self.pp.dstLayerD:

            if len(self.pp.dstLayerD[locus]) == 0:
                exitstr = 'EXITING, no dates defined in Ancillary.OrganizeAncillary'
                exit(exitstr)
            
            for datum in self.pp.dstLayerD[locus]:

                if len(self.pp.dstLayerD[locus][datum]) == 0:

                    exitstr = 'EXITING, no compositions defined in Ancillary.OrganizeAncillary'
                    
                    print (exitstr)

                for comp in self.pp.dstLayerD[locus][datum]:
                                            
                    if len(self.pp.process.parameters.replacestr) > 1:
                        SNULLE
                        srcraw = self._ExpandAncillaryImport(locus,datum,comp)
                    
                    else:                    
                        
                        self.dstLayer = self.pp.dstLayerD[locus][datum][comp] 
                                                
                        srcraw = self.pp.srcRawD[comp]
                        
                        #Create the source layer
                        self._SrcLayer(srcraw)
                        
                        if self.verbose > 1:
                        
                            infostr = '        Importing: %s' %(self.srcFPN)
                            
                            print (infostr)
                    
                    if self.pp.process.parameters.importcode in ['climateindex']:

                        #self._SrcLayer(srcraw)
                        
                        self._ReadClimateIndex(self.srcFPN,comp)
                        
                        continue 
                    
                    if self.pp.process.parameters.importcode in ['co2record']:

                        #self._SrcLayer(srcraw)
                        
                        self._ReadCO2records(self.srcFPN,comp)
                        
                        continue    
                    
                    if not self.dstLayer._Exists() or self.pp.process.overwrite: 
                                
                        #self._SrcLayer(srcraw)

                        if not os.path.isfile(self.srcFPN):
                            
                            warnstr = 'The ancillary source file %(fpn)s can not be found, skipping' %{'fpn':self.srcFPN}
                            
                            print (warnstr)

                            continue
                        
                        elif self.dstLayer.comp.celltype.lower() in ['none','csv','txt']:
                        
                            self._ImportText()
                        
                        elif self.dstLayer.comp.celltype.lower() == 'vector':
                        
                            self._ImportVector()
                        
                        else:
  
                            self._ImportRaster() 
                           
                    self._UpdateDB(self.dstLayer,comp)
 

    def _ExpandAncillaryImport(self, locus, datum, comp):
        from copy import deepcopy
        '''
        '''
        if len(self.process.proc.replaceD) == 0:
            print (self.process.proc.replaceD)
            FISHYERROR
        for rpl in self.process.proc.replaceD:
            if rpl == 'copydatum':
                print ('Ancillary import, copying datum')
                for attr in self.process.proc.replaceD[rpl]:
                    if attr == 'compinattribute':
                        strObj = self.process.proc.replaceD[rpl][attr]

                        srcrawD = deepcopy(self.process.proc.srcraw.paramsD[comp])
                        searchStr = self.pp.process.parameters.replacestr
                        replaceStr = datum
                        srcrawD[strObj] = srcrawD[strObj].replace(searchStr,replaceStr)
            elif rpl == 'copydatum+month':
                #Added the handle the IMERG data that has both date (YYYYMMDD) and MM in filename
                searchStrL = [self.pp.process.parameters.replacestr, 'MM']
                replaceStrL = [datum, datum[4:6]]
                for attr in self.process.proc.replaceD[rpl]:
                    
                    if attr == 'compinattribute':
                        srcrawD = deepcopy(self.process.proc.srcraw.paramsD[comp])
                        for m,searchStr in enumerate(searchStrL):
                            replaceStr = replaceStrL[m] 
                            strObj = self.process.proc.replaceD[rpl][attr]

                            srcrawD[strObj] = srcrawD[strObj].replace(searchStr,replaceStr)
            elif rpl == 'datum':
                for attr in self.process.proc.replaceD[rpl]:
                    if attr == 'compinattribute':
                        strObj = self.process.proc.replaceD[rpl][attr]
                        srcrawD = deepcopy(self.process.proc.srcraw.paramsD[comp])
                        
                        
                        searchStr = self.pp.process.parameters.replacestr
                        replaceStr = datum
                        for item in strObj:
                            srcrawD[item] = srcrawD[item].replace(searchStr,replaceStr)
            else:
                print ('rpl',rpl)
                ADDREPLACEFUNCTION
            return srcrawD
          
    def _SrcLayer(self, srcraw ):
        '''
        '''
        
        if self.pp.srcPath.hdr[0] == '.':
        
            ext = self.pp.srcPath.hdr
       
        else:
        
            ext = '.%s' %(self.pp.srcPath.hdr)
            
        if srcraw.datafile.endswith(ext):
        
            self.srcFN = srcraw.datafile  
            
        else:  
            
            self.srcFN = '%(fn)s%(e)s' %{'fn':srcraw.datafile,'e':ext}        
        
        if self.pp.srcPath.volume in ['','.','None']:
            
            # indicates a relative path
            self.srcFP = os.path.join('.', srcraw.datadir)

        else:
        
            self.srcFP = os.path.join('/Volumes', self.pp.srcPath.volume, srcraw.datadir)
        
        self.srcFPN = os.path.join(self.srcFP,self.srcFN)
        
        print ('Ancillary source file', self.srcFPN)

    def _ImportVector(self):
        '''
        '''
        
        if self.verbose:
            printstr = '    importing vector: %(srcfpn)s\n        to: %(dstfpn)s' %{'srcfpn':self.srcFPN, 'dstfpn':self.dstLayer.FPN}
            print (printstr)
            
        spatialRef = GetVectorProjection(self.srcFPN)
        
        gdalcmd = '/Library/Frameworks/GDAL.framework/Programs/ogr2ogr -skipfailures '
        
        #gdalcmd = ['/Library/Frameworks/GDAL.framework/Programs/ogr2ogr', '-skipfailures']
                
        if not spatialRef.epsg:
        
            epsg = ' EPSG:%(epsg)d' %{'epsg': int(self.pp.process.parameters.epsg)}
            
            #gdalcmd.extend( [ '-a_srs', epsg])
            
            gdalcmd += '-a_srs %s ' %(epsg)
            
                
        else:
        
            if spatialRef.epsg == 4326:
            
                pass
            
            else:
                #gdalcmd.extend( ['-t_srs', 'EPSG:4326' ] )
                gdalcmd += '-t_srs EPSG:4326 '
                
        #gdalcmd.extend([self.dstLayer.FPN, self.srcFPN  ])
        
        gdalcmd += '%(dst)s %(src)s' %{'dst': self.dstLayer.FPN, 'src':self.srcFPN}
        
        
        subprocess.call(gdalcmd, shell=True)
       

        
    def _ImportRaster(self):
        '''
        '''
        
        if self.verbose:
            print ('    Importing raster')

        if self.process.srcpath.hdrfiletype.lower() == 'lis':
            '''This is a very special format, only applies to gghydro'''
            ancillary_import.GGHtranslate(self.Lin.FPN,self.Lout.FPN,self.Lout.comp.celltype,self.Lout.comp.cellnull,False)
            
        elif self.process.srcpath.hdrfiletype.lower() == '1x1':
            '''This is a very special format, only applies to stillwell'''
            ancillary_import.StillwellTranslate(self.Lin.FPN,self.Lout.FPN,self.Lout.comp.celltype,self.Lout.comp.cellnull,False)
            
        elif self.pp.process.parameters.importcode.lower() == 'trmm':
            '''This is a very special format, only applies to TRMM data with north to the right'''
            #ancillary_import.TRMMTranslate(self.Lout.comp, self.Lin.FPN,self.Lout.FPN,False)
            ancillary_import.TRMMTranslate(self.srcFPN, self.dstLayer.FPN, self.dstLayer.comp, False)
            
        elif self.pp.process.parameters.importcode.lower() == 'imerg':
            '''This is a very special format, only applies to IMERG data'''
            #ancillary_import.TRMMTranslate(self.Lout.comp, self.Lin.FPN,self.Lout.FPN,False)
            ancillary_import.IMERGTranslate(self.srcFPN, self.dstLayer.FPN, self.dstLayer.comp, self.datum, False)
            
        elif self.pp.process.parameters.importcode.lower() == 'grace':
            '''This is a very special format, only applies to TRMM data with north to the right'''
            #ancillary_import.TRMMTranslate(self.Lout.comp, self.Lin.FPN,self.Lout.FPN,False)
            if not self.dstLayer.comp.celltype == 'Float32':
                SNULLE
            if not self.dstLayer.comp.cellnull == 32767:
                print (self.dstLayer.comp.cellnull)
                SNULLE
            ancillary_import.GRACETranslate(self.srcFPN, self.dstLayer.FPN, self.dstLayer.comp, False)
        
        elif self.pp.process.parameters.importcode.lower() == 'ascii':
            self.gdaldriver = 'AAIGrid'
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/gdal_translate '
            gdalcmd = '%(s1)s -ot %(ct)s' %{'s1':gdalcmd, 'ct':self.dstLayer.comp.celltype}
            gdalcmd = '%(s1)s -a_srs EPSG:%(srs)s' %{'s1':gdalcmd, 'srs':self.pp.process.parameters.epsg} 
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':self.srcFPN, 'tar':self.dstLayer.FPN}
            os.system(gdalcmd)
            
        elif self.pp.process.parameters.importcode.lower() == 'geoitff' or self.process.srcpath.hdrfiletype.lower() == 'tif':
            #The src is a standard geotiff, get the spatialRef and the metaData
            spatialRef, metadata = GetRasterMetaData(self.srcFPN)
            spatialRefDiff = False
            if self.pp.process.parameters.epsg != 0:
                srs = MjProj()
                srs.SetFromEPSG(self.pp.process.parameters.epsg)
                srs.SetProj4()
                #print ('proj4',srs.proj4)
                if srs.proj4 != spatialRef.proj4:
                    spatialRefDiff = True

            nullDiff = False
            if self.dstLayer.comp.cellnull != metadata.cellnull:
                warnstr = 'Warning - cellnull definition differs'
                print (warnstr)
                nullDiff = True
            typeDiff = False
            if self.dstLayer.comp.celltype.lower() != metadata.celltype.lower():
                warnstr = 'Warning - celltype definition differs'
                print (warnstr)
                typeDiff = True
                

            if spatialRefDiff:
                gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/gdalwarp '

                gdalcmd = '%(s1)s -t_srs "%(srs)s" ' %{'s1':gdalcmd, 'srs':srs.proj4}
                if self.process.parameters.resol == 0:
                    exitmsg = 'To warp the dataset you need to set the target EPSG and resolution' %(os.path.split(self.Lin.FPN)[1], self.Lin.comp.spatialRef.epsg, self.process.parameters.resol)
                    exit(exitmsg)
                
                gdalcmd = '%(s1)s -tr %(tr)s %(tr)s ' %{'s1':gdalcmd, 'tr':self.process.parameters.resol}
                if  len(self.process.parameters.ext) > 10:
                    xmin,ymin,xmax,ymax = self.process.parameters.ext.split(',')
                    gdalcmd = '%(s1)s -te %(xmin)s %(ymin)s %(xmax)s %(ymax)s ' %{'s1':gdalcmd, 'xmin':xmin, 'ymin':ymin, 'xmax':xmax, 'ymax':ymax}

                if nullDiff:
                    NOTDONE
                
            elif nullDiff:
                gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/gdal_translate '
                if setEpsg:
                    gdalcmd = '%(s1)s -a_srs "%(srs)s" ' %{'s1':gdalcmd, 'srs':srs.proj4}
   
                gdalcmd = '%(s1)s -a_nodata %(null)s ' %{'s1':gdalcmd, 'null':self.Lout.comp.cellnull}
            else:
                gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/gdalmanage copy '
            
            gdalcmd = ' %(s1)s %(src)s %(tar)s\n' %{'s1':gdalcmd, 'src':self.srcFPN, 'tar':self.dstLayer.FPN}
            print (gdalcmd)

            os.system(gdalcmd)
        elif self.pp.process.parameters.importcode == 'srtm' and self.process.srcpath.hdrfiletype == 'nc':
            print ('importing srtm nc file')
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/gdal_translate '
            gdalcmd = ' %(s1)s %(src)s %(tar)s\n' %{'s1':gdalcmd, 'src':self.srcFPN, 'tar':self.dstLayer.FPN}
            print (gdalcmd)
            os.system(gdalcmd)
        else:
            print (self.pp.process.parameters.importcode)
            print (self.Lin.FPN,self.Lout.FPN)
            print (self.Lin.comp.dat)
            print (self.Lin.comp.band)
            BALLE

    def ImportVariousLayersOLD(self):   

        #start with metadata
        #check if there is an xml file 
        metaxml = '%(s)s.xml' %{'s':self.Lin.FPN}
        if os.path.isfile(metaxml):
            tarmetaxml =  '%(s)s.xml' %{'s':self.Lout.FPN}
            cmd = 'mv %(src)s %(tar)s' %{'src':metaxml, 'tar':tarmetaxml}
            os.system(cmd)
        #get any palette
        palette = False
        '''
        if self.Lin.comp.hdr == 'shp':
            pass
        else:
            print self.Lout.comp.palette
            if self.Lout.comp.palette.lower() in ['none','n','false','']:
                palette = False
            else:
                palette = ConnLayout.SelectPalette(self.Lout.comp.palette)
        '''
        #find any registered metadata
        if self.Lin.comp.hdr == 'shp':
            #check if the shape file is projected:
            self.Lin.GetVectorProjection()
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/ogr2ogr -skipfailures'
            if not self.Lin.spatialRef.epsg:
                #mj_proj = mj_gis.MjProj()
                #mj_proj.SetFromEPSG(int(self.ancilDS.epsg))
                #print self.process.parameters.epsg
                gdalcmd = ' %(s1)s -a_srs EPSG:%(epsg)d' %{'s1':gdalcmd, 'epsg': int(self.process.parameters.epsg)}
                #DOUBLETRANS #First set SRS then transform
            else:
                if self.Lin.spatialRef.epsg == 4326:
                    pass
                else:
                    gdalcmd = ' %(s1)s -t_srs EPSG:4326 ' %{'s1':gdalcmd}
                    #gdalcmd = ' %(s1)s -t_srs %(srs)s ' %{'s1':gdalcmd, 'srs': self.Lin.spatialRef.proj_cs}
                
            gdalcmd = ' %(s1)s %(dst)s %(src)s' %{'s1':gdalcmd, 'dst': self.Lout.FPN, 'src':self.Lin.FPN}

            os.system(gdalcmd)

        elif self.Lin.comp.hdr == 'e00' and self.Lout.comp.hdr == 'shp':
            #cmd = '/Applications/e00compr-1.0.1/e00conv /Volumes/mjtrans/ANCILRAW/GRID-arendal/global-wild/glowil00/wilderness.e00 /Volumes/mjtrans/ANCILRAW/GRID-arendal/global-wild/glowil00/temp00'
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/ogr2ogr -skipfailures'
            gdalcmd = ' %(s1)s %(dst)s %(src)s' %{'s1':gdalcmd, 'dst': self.Lout.FPN, 'src':self.Lin.FPN}
            os.system(gdalcmd)
            
        elif self.Lin.comp.hdr.lower() == 'lis':
            '''This is a very special format, only applies to gghydro'''
            from ancillary_import_v73 import GGHtranslate
            GGHtranslate(self.Lin.FPN,self.Lout.FPN,self.Lout.comp.celltype,self.Lout.comp.cellnull,palette)
            
        elif self.Lin.comp.dat.lower() == '1x1':
            '''This is a very special format, only applies to stillwell'''
            from ancillary_import_v73 import StillwellTranslate
            StillwellTranslate(self.Lin.FPN,self.Lout.FPN,self.Lout.comp.celltype,self.Lout.comp.cellnull,palette)
            
        elif self.Lin.comp.dat.lower() == 'trmm':
            '''This is a very special format, only applies to TRMM data with north to the right'''
            from ancillary_import_v73 import TRMMTranslate
            TRMMTranslate(self.Lout.comp, self.Lin.FPN,self.Lout.FPN,palette)

        
        elif self.Lin.comp.hdr.lower() in self.GDALhdrL: 
            self.Lin.filetype = self.Lin.comp.hdr.lower()
            '''
            self.Lin.GetRastermetadata()
            '''
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            '''
            if self.Lin.spatialRef.epsg == None:
                self.Lout.TGprojection(self.pileC.epsg)
                gdalcmd = '%(s1)s -a_srs %(srs)s' %{'s1':gdalcmd, 'srs':self.Lout.projection}
            print  self.Lin.FPN
            '''
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':self.Lin.FPN, 'tar':self.Lout.FPN}
            print (gdalcmd)

            os.system(gdalcmd)
            mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)

        elif self.Lin.comp.hdr.lower() in ['hdr','.hdr'] and self.Lin.comp.dat.lower() in ['bil','.bil']:
            ancilBilFPN = self.Lin.FPN.replace('.hdr','.bil')
            self.Lin.filetype = 'bil'
            self.Lin.FPN = ancilBilFPN
            self.Lin.GetRastermetadata()
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            if self.Lin.spatialRef.epsg == None:
                self.Lout.TGprojection(self.Lin.pileC.epsg)
                gdalcmd = '%(s1)s -a_srs %(srs)s' %{'s1':gdalcmd, 'srs':self.Lout.projection}
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':ancilBilFPN, 'tar':self.Lout.FPN} 
            os.system(gdalcmd)
            mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)
        
        elif os.path.isdir(self.Lin.FPN):
            self.Lin.GetRastermetadata()
            '''Data in folder, arcview raster format'''
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            #TGTODO handel all projections better
            if self.Lin.spatialRef.epsg == None:
                gdalcmd = '%(s1)s -a_srs EPSG:%(epsg)d' %{'s1':gdalcmd, 'epsg':int(self.Lin.ancilDS.epsg)}
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':self.Lin.FPN, 'tar':self.Lout.FPN} 
            os.system(gdalcmd)
            mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)
            
        elif self.Lin.comp.hdr.lower() in ['asc','.asc.'] or self.Lin.comp.dat.lower() in ['aai','.aai.']: 
            #Arc/Info ASCII Grid 
            self.Lin.filetype = self.Lin.comp.hdr.lower()
            self.Lin.FPN = self.Lin.FPN
            self.gdaldriver = 'AAIGrid'
            gdalcmd = '/Library/Frameworks/GDAL.framework/Versions/1.11/Programs/gdal_translate '
            gdalcmd = '%(s1)s -ot %(ct)s' %{'s1':gdalcmd, 'ct':self.Lout.comp.celltype}
            #gdalcmd = '%(s1)s -a_nodata %(cn)s' %{'s1':gdalcmd, 'cn':self.Lout.comp.cellnull}
            gdalcmd = '%(s1)s -a_srs EPSG:%(srs)s' %{'s1':gdalcmd, 'srs':self.process.parameters.epsg} 
            gdalcmd = '%(s1)s %(src)s %(tar)s' %{'s1':gdalcmd, 'src':self.Lin.FPN, 'tar':self.Lout.FPN}
            print (gdalcmd)

            os.system(gdalcmd)
            #mj_gis.ReplaceRasterDS(self.Lout.FPN,palette=palette)
        
        else:
            exitstr = 'unknown file type in ImportLayer',self.Lin.comp.hdr
            print (exitstr)
            BALLE
            sys.exit(exitstr)         
        #Check projection, and add if needed
        if self.Lin.zip:
            self.RemoveTemporary()
                 
    def _ImportText(self):
        if self.verbose:
            printstr = '    importing text file: %(srcfpn)s\n        to: %(dstfpn)s' %{'srcfpn':self.srcFPN, 'dstfpn':self.dstLayer.FPN}
            print (printstr)
        copyfile(self.srcFPN,self.dstLayer.FPN)
           
    def _AncilTxtToDb(self,session):
        
        for locus in self.process.srcLayerD:
            for datum in self.process.srcLayerD[locus]:
                for comp in self.process.srcLayerD[locus][datum]:
                    self._SrcLayer = self.process.srcLayerD[locus][datum][comp]
                    if not os.path.isfile(self.srcLayer.FPN):
                        warnstr = 'The ancillary source file %(fpn)s can not be found, skipping' %{'fpn':self.srcLayer.FPN}
                        print (warnstr)
                        SNULELBULLE
                        continue
                    
                    if self.pp.process.parameters.template == 'climateindex':
                        self._ReadClimateIndex()
                        
    def _ReadClimateIndex(self,srcFPN,comp):
        import csv
        print (srcFPN)
        print ()
        srcCellNull = self.process.proc.srcraw.paramsD[comp]['cellnull']
        dstCellNull = self.dstLayer.comp.cellnull
        print ('srcCellNull',srcCellNull)
        if not self.process.proc.srcraw.paramsD[comp]['id'] == self.process.proc.srcraw.paramsD[comp]['datafile']:
            exitstr = 'Climateindex import: the id and the datafile should have the same name (%s vs %s)'  %(self.process.proc.srcraw.paramsD[comp]['id'],self.process.proc.srcraw.paramsD[comp]['datafile'])
            exit (exitstr)
        queryL = []

        with open(srcFPN) as f:
            reader = csv.reader(f, delimiter=' ', skipinitialspace = True)
            startyear, endyear = next(reader)
            #print (startyear,endyear)

            for row in reader:
                y = row[0]
                for m in range(1,13):
                    acqdate = mj_dt.yyyy_mm_dd_Date(y,m,1)
                    acqdatestr = mj_dt.DateToStrDate(acqdate)[0:6]
                    value = row[m]
                    
                    if y == endyear and float(value) == srcCellNull:
                        continue
                    if float(value) == srcCellNull:
                        value = dstCellNull
                    queryL.append({'index':self.process.proc.srcraw.paramsD[comp]['id'], 'acqdate':acqdate,'acqdatestr':acqdatestr,'value':value})
                if y == endyear:
                    break
            #After the last year, the next row is the nodata
            cellNull = next(reader)[0]
        if not float(cellNull) == srcCellNull:
            exitstr = 'cellnull for climateindex %s is not correct, should be: %s' %(comp, cellNull)
        self.session._InsertClimateIndex(queryL)
        
    def _ReadCO2records(self,srcFPN,comp):
        import csv

        srcCellNull = self.process.proc.srcraw.paramsD[comp]['cellnull']
        dstCellNull = self.dstLayer.comp.cellnull

        if not self.process.proc.srcraw.paramsD[comp]['id'] == self.process.proc.srcraw.paramsD[comp]['datafile']:
            exitstr = 'CO2record import: the id and the datafile should have the same name (%s vs %s)'  %(self.process.proc.srcraw.paramsD[comp]['id'],self.process.proc.srcraw.paramsD[comp]['datafile'])
            exit (exitstr)
        queryL = []

        with open(srcFPN) as f:
            reader = csv.reader(f, delimiter=',', skipinitialspace = True)
            header = next(reader)

            for row in reader:
                print ('row',row)
                
                acqdate = mj_dt.yyyy_mm_dd_Str_ToDate(row[0])
                acqdatestr = mj_dt.DateToStrDate(acqdate)[0:6]
                value = row[3]
                

                if float(value) == srcCellNull:
                    value = dstCellNull
                queryL.append({'index':self.process.proc.srcraw.paramsD[comp]['id'], 'acqdate':acqdate,'acqdatestr':acqdatestr,'value':value})

        self.session._InsertClimateIndex(queryL)
      
    def _UpdateDB(self, layer, comp):
        '''
        '''
        
        '''
        srcrawD = self.process.proc.srcraw.paramsD[comp]
        if self.process.proc.userProj.system == 'specimen':
            system = 'specimen'
        else:
            system = 'ancillary'
        '''
 
        queryD = dict ( list ( self.pp.process.parameters.__dict__.items() ) )
        
        queryD['system'] = self.pp.procsys.dstsystem
        
        queryD['dsid'] = self.dsid
        
        self.session._ManageAncilDS(queryD, self.pp.process.overwrite, self.pp.process.delete)
        
        self.session._InsertCompDef( layer.comp, self.pp.process.parameters.title, self.pp.process.parameters.label )
        
        self.session._LinkDsCompid(self.dsid, layer.comp.compid, self.pp.process.overwrite, self.pp.process.delete)
        
        self.session._InsertCompProd(layer.comp)

        self.session._InsertLayer(layer, self.pp.process.overwrite, self.pp.process.delete)
