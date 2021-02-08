'''
Created on 22 Jan 2021

@author: thomasgumbricht
'''

#imports
from __future__ import division
import sys
import gdal
from gdalconst import *
import array as arr
import struct
from osgeo import osr
import os
import numpy as np
from support import karttur_dt as mj_dt

#import mj_datetime_v70 as mj_dt

class Composition:
    def __init__(self,celltype,cellnull):
        """The constructoris just an empty container.""" 
        self.celltype = celltype
        self.cellnull = cellnull

def FixGDALPalette(paletteT):
    #paletteT = mj_psycopg2.SelectPalettePub(palette)
    if len(paletteT) == 0:
        return False
    PcR = []
    AT = []
    ATvalue = []
    ATattr = []
    for c in range(len(paletteT)):
        cr = (paletteT[c][0],(paletteT[c][1],paletteT[c][2],paletteT[c][3]))
        PcR.append(cr)
        ATvalue.append(paletteT[c][0])
        ATattr.append(paletteT[c][5])
    for a in range(paletteT[c][0]): #Up to the highest attibute
        if a in ATvalue:
            x = ATvalue.index(a)
            AT.append(ATattr[x])
        else:
            AT.append('')
    return PcR,AT,paletteT[c][0]

def RasterPalette(paletteT):
        PcR,AT,maxAT = FixGDALPalette(paletteT)
        ct = gdal.ColorTable() 
        '''
        For discrete colors
        #ct.CreateColorRamp(0,(178,223,138),5,(255,127,0))
        #ct.CreateColorRamp(Pcr)
        for c in PcR:

            ct.SetColorEntry(c[0],c[1])
        '''
        #for color ramps
        for c in range(1,len(PcR)):
            ct.CreateColorRamp(PcR[c-1][0],PcR[c-1][1],PcR[c][0],PcR[c][1])
        return ct
        '''
        dst_ds.GetRasterBand(1).SetColorTable(ct) 
        
        rat = gdal.RasterAttributeTable()
        rat.CreateColumn("Value", GFT_String, GFT_String)
        for i in range(maxAT): 
            rat.SetValueAsString(i, 0, AT[i])
        dst_ds.GetRasterBand(1).SetDefaultRAT(rat)
        '''

def GGHtranslate(inFPN,outFPN,celltype,cellnull,palette):
    ''' Special routine for importing gghydro data, it has very special format
    '''
    mem_drv = gdal.GetDriverByName( 'MEM' )
    if celltype == 'Byte':
        dsOut = mem_drv.Create('', 360, 180, 1, gdal.GDT_Byte)
        valueArray = arr.array('B',(0,)*360)
    elif celltype == 'Int16':
        dsOut = mem_drv.Create('', 360, 180, 1, gdal.GDT_Int16)
        valueArray = arr.array('h',(0,)*360)
    else:
        sys.exit('Fix the datatype, either in db or in script')
    #dsquery.GetRasterBand(1).Fill(_null)
    for line in open(inFPN):  # opened in text-mode; all EOLs are converted to '\n'
        line = line.rstrip('\n')
        #Read the first two records, that represent lon lat
        if len(line) < 10:
            continue
        for c in range (182):
            if c == 0:
                c0 = 0
                c1 = 4
                posx = int(line[c0:c1])
                posx -= 180
                posx = abs(posx)
            elif c == 1:
                c0 = 4
                c1 = 8
                posy = int(line[c0:c1])
                posy += 90
                posy *= -1
                posy += 179
            else:
                c0 = c*5-2
                c1 = c*5+3
                valueArray[c-2] = int(line[c0:c1])
        #convert to numpy format and write to output
        if celltype.lower() in ['uint8','byte']:
            values = struct.pack('B'*len(valueArray), *valueArray)
        elif celltype == 'Int16':
            values = struct.pack('h'*len(valueArray), *valueArray)
        else:
            sys.exit('something wrong with data type, check the script')
        dsOut.WriteRaster( posx, posy, 180, 1, values)
    # Output driver, use geotiff
    driver = gdal.GetDriverByName ( "GTiff" )
    #The projection is laonlat, with 1 degree spatial resolution
    proj = osr.SpatialReference()  
    proj.SetWellKnownGeogCS( "EPSG:4326" )  
    dsOut.SetProjection(proj.ExportToWkt())  
    geotransform = (-180.0, 1.0, 0.0, 90.0, 0.0, -1.0)  
    dsOut.SetGeoTransform(geotransform)
    # Create a copy of the in memory dataset `reprojected_dataset`, and save it
    dst_ds = driver.CreateCopy( outFPN, dsOut, 0 ) 
    dst_ds.GetRasterBand(1).SetNoDataValue(cellnull)
    if palette:
        ct = RasterPalette(palette)
        dst_ds.GetRasterBand(1).SetColorTable(ct) 
    #Get the extension box and resolution of the dataset, i.e. the geotransform
    dst_ds = None        
    dsOut = None # Flush the dataset to disk

def StillwellTranslate(inFPN,outFPN,celltype,cellnull,palette):
    mem_drv = gdal.GetDriverByName( 'MEM' )
    if celltype.lower() in ['uint8','byte']:
        dsOut = mem_drv.Create('', 360, 180, 1, gdal.GDT_Byte)
        valueArray = arr.array('B')
    elif celltype == 'Int16':
        dsOut = mem_drv.Create('', 360, 180, 1, gdal.GDT_Int16)
        valueArray = arr.array('h')
    else:
        print ('Unknown datatype', dsDict['datatyp'])
        sys.exit('Fix the datatype, either in db or in script')
    #dsquery.GetRasterBand(1).Fill(_null)
    l = 0
    for line in open(inFPN):  # opened in text-mode; all EOLs are converted to '\n'
        l += 1       
        if l > 4:
            line = line.rstrip('\n')
            #Read the first two records, that represent lon lat
            for c in range (363):
                if c > 2:
                    c0 = c*2
                    c1 = c*2+2 
             
                    if line[c0:c1] == '  ':
                        #p = (l-5)*360+c-4
                        valueArray.append(255)
                    else:
                        #print l, c-4, c0, c1, line[c0:c1]
                        #valueArray[c-4] = int(line[c0:c1])
                        valueArray.append(int(line[c0:c1] ))
                    #Write the data to the raster image
    #print len(valueArray)
    if celltype.lower() in ['uint8','byte']:
        values = struct.pack('B'*len(valueArray), *valueArray)
    elif celltype == 'Int16':
        values = struct.pack('h'*len(valueArray), *valueArray)
    else:
        sys.exit('something wrong with data type, check the script')
    dsOut.WriteRaster( 0, 0, 360, 180, values)
    #print c-2, c0, c1, valueArray[c-2]
    # Output driver, as before
    driver = gdal.GetDriverByName ( "GTiff" )
    proj = osr.SpatialReference()  
    proj.SetWellKnownGeogCS( "EPSG:4326" )  
    dsOut.SetProjection(proj.ExportToWkt())  
    geotransform = (-180.0, 1.0, 0.0, 90.0, 0.0, -1.0)  
    dsOut.SetGeoTransform(geotransform)
    dsOut.GetRasterBand(1).SetNoDataValue(cellnull)
    if palette:
        ct = RasterPalette(palette)
        dsOut.GetRasterBand(1).SetColorTable(ct)
    #set null

    # Create a copy of the in memory dataset `reprojected_dataset`, and save it
    dst_ds = driver.CreateCopy( outFPN, dsOut, 0 ) 
    #Get the extension box and resolution of the dataset, i.e. the geotransform           
    dst_ds = None # Flush the dataset to disk
    dsOut = None
    #print cellsize
    #print minx,maxx,miny,maxy
    
def GRACETranslate(inFPN,outFPN,comp,palette):
    mem_drv = gdal.GetDriverByName( 'MEM' )
    if comp.celltype.lower() in ['uint8','byte']:
        dsOut = mem_drv.Create('', 360, 180, 1, gdal.GDT_Byte)
        valueArray = arr.array('B')
    elif comp.celltype == 'Int16':
        dsOut = mem_drv.Create('', 360, 180, 1, gdal.GDT_Int16)
        valueArray = arr.array('h')
    elif comp.celltype == 'Float32':
        dsOut = mem_drv.Create('', 360, 180, 1, gdal.GDT_Float32)
        valueArray = arr.array('f')
    else:
        print ('Unknown datatype', dsDict['datatyp'])
        sys.exit('Fix the datatype, either in db or in script')
    #dsquery.GetRasterBand(1).Fill(_null)
    a = np.zeros(shape=(360,180))
    metaD = {}
    for line in open(inFPN):  # opened in text-mode; all EOLs are converted to '\n'
        if line[0:3] == 'HDR':
            #GetGraceMeta()  
            l = line[4:len(line)-1].split('=') 
            metaD[l[0]] = l[1]
            
    #Check that the input corresponds with the metaD
    acqdate = metaD['time_start']
    cellnull = metaD['_FillValue']
    dataunit = metaD['units']
    if float(cellnull) != comp.cellnull:
        BALLE
    if dataunit != comp.dataunit:
        BALLE

    for line in open(inFPN):  # opened in text-mode; all EOLs are converted to '\n'
        if line[0:3] == 'HDR':
            pass
        else:
            line = line.rstrip('\n')
            l = line.split()

            lon = int(float(l[0])-0.5-180)
            if lon < 0:
                lon += 360
            lat = int(float(l[1])-0.5+90)

            valueArray.append(float(l[2]))
            a[lon,lat] = float(l[2])
    outBand = dsOut.GetRasterBand(1)
    # write the data
    outBand.WriteArray(np.flipud(np.transpose(a)), 0, 0)

    #outBand.SetNoDataValue(comp.cellnull)
    #print c-2, c0, c1, valueArray[c-2]
    # Output driver, as before
    driver = gdal.GetDriverByName ( "GTiff" )
    proj = osr.SpatialReference()  
    proj.SetWellKnownGeogCS( "EPSG:4326" )  
    dsOut.SetProjection(proj.ExportToWkt())  
    geotransform = (-180.0, 1.0, 0.0, 90.0, 0.0, -1.0)  
    dsOut.SetGeoTransform(geotransform)
    dsOut.GetRasterBand(1).SetNoDataValue(comp.cellnull)
    if palette:
        ct = RasterPalette(palette)
        dsOut.GetRasterBand(1).SetColorTable(ct)
    #set null

    # Create a copy of the in memory dataset `reprojected_dataset`, and save it
    dst_ds = driver.CreateCopy( outFPN, dsOut, 0 ) 
    #Get the extension box and resolution of the dataset, i.e. the geotransform           
    dst_ds = None # Flush the dataset to disk
    dsOut = None

def TRMMTranslate(srcFPN, dstFPN, comp, palette):
    #import numpy as np
    from geoimagine.gis.mj_gis_v80 import RasterOpenGetFirstLayer, MjProj, RasterDataSource, RasterLayer
    #from mj_gis_v80 import 
    srcFP, srcFN = os.path.split(srcFPN)
    
    tmpFPN = os.path.join(srcFP,'tmp.tif')
    if os.path.isfile(tmpFPN):
        os.remove(tmpFPN)

    #oscmd = '/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/gdal_translate HDF4_SDS:UNKNOWN:"%(in)s"' %{'in':inFPN}

    oscmd = '/Library/Frameworks/GDAL.framework/Versions/2.1/Programs/gdal_translate HDF4_SDS:UNKNOWN:"%(src)s"' %{'src':srcFPN}
    if comp.band == 'trmm-3b43v7-precip':
        oscmd = '%(cmd)s:0:precipitation %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}
    elif comp.band == 'trmm-3b43v7-relerr':
        oscmd = '%(cmd)s:1:relativeError %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}
    elif comp.band == 'trmm-3b43v7-gauge-weight':
        oscmd = '%(cmd)s:2:gaugeRelativeWeighting %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}
    else:
        print ('unrecognised band',comp.band)
        STOP
    
    os.system(oscmd)

    yyyymmdd = srcFN.split('.')[1]

    startDate = mj_dt.yyyymmddDate(yyyymmdd)
    endDate = mj_dt.AddMonth(startDate,1)
    days = mj_dt.GetDeltaDays(startDate, endDate)
    
    srcDS,srcLayer = RasterOpenGetFirstLayer(tmpFPN,'read')
    #Rotate
    srcLayer.ReadBand()
    srcLayer.NPBAND
    #np.rot90(srcLayer.NPBAND)

    #swap x and y
    XSize = srcLayer.layer.YSize
    YSize = srcLayer.layer.XSize
    #set pixelsiae:
    pixelSize = 0.25
    minX = -180
    maxY = 50
    gt = (minX, pixelSize, 0, maxY, 0, -pixelSize)
    spatialRef = MjProj()
    spatialRef.SetFromEPSG(4326)
    spatialRef.SetGeoTrans(gt)
    
    tarDS = RasterDataSource()
    
    tarLayer = RasterLayer()
    tarLayer.cols = XSize
    tarLayer.lins = YSize
    tarLayer.geotrans = gt
    tarLayer.projection = spatialRef.proj_cs.ExportToWkt()


    BAND = np.rot90(srcLayer.NPBAND)

    if comp.band == 'trmm-3b43v7-gauge-weight':
        #BAND = BAND*100 #relative weight converted to percent, no it seems to be percent already
        BAND.astype(np.uint8)
        #BALLE
    else:
        BAND = BAND*days.days*24 #hourly rainfall converted to monthly
        BAND.astype(np.int16)
        if np.min(BAND) < 0:
            print ('nodata in',srcFPN)
            BAND[BAND < 0] = -32768
    
    tarLayer.BAND = BAND

    tarLayer.SetSpatialRef(spatialRef)

    tarLayer.comp = comp
    
    tarDS.CreateGDALraster(dstFPN,tarLayer) 
    
    srcDS.CloseDS()
    tarDS.CloseDS()
    
def IMERGTranslate(srcFPN, dstFPN, comp, yyyymmdd, palette):
    #import numpy as np
    from geoimagine.gis.mj_gis_v80 import RasterOpenGetFirstLayer, MjProj, RasterDataSource, RasterLayer
    #from mj_gis_v80 import 
    srcFP, srcFN = os.path.split(srcFPN)
    
    tmpFPN = os.path.join(srcFP,'tmp.tif')
    if os.path.isfile(tmpFPN):
        os.remove(tmpFPN)

    oscmd = '/Library/Frameworks/GDAL.framework/Versions/2.2/Programs/gdal_translate HDF5:"%(src)s"' %{'src':srcFPN}

    if comp.band == 'imerg-3bv05b-precip':
        oscmd = '%(cmd)s://Grid/precipitation %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}
    elif comp.band == 'imerg-3bv05b-relerr':
        oscmd = '%(cmd)s://Grid/randomError %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}
    elif comp.band == 'imerg-3bv05b-quality':
        oscmd = '%(cmd)s://Grid/precipitationQualityIndex %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}
    elif comp.band == 'imerg-3bv05b-liquid':
        oscmd = '%(cmd)s://Grid/probabilityLiquidPrecipitation %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}
    elif comp.band == 'imerg-3bv05b-gauge-weight':
        oscmd = '%(cmd)s://Grid/gaugeRelativeWeighting %(tmp)s' %{'cmd':oscmd, 'tmp':tmpFPN}

    else:
        print ('unrecognised band',comp.band)
        JAHGFASFGJKAS

    os.system(oscmd)

    startDate = mj_dt.yyyymmddDate(yyyymmdd)
    endDate = mj_dt.AddMonth(startDate,1)
    days = mj_dt.GetDeltaDays(startDate, endDate)
    
    srcDS,srcLayer = RasterOpenGetFirstLayer(tmpFPN,'read')

    srcLayer.ReadBand()
    srcLayer.NPBAND

    #swap x and y
    XSize = srcLayer.layer.YSize
    YSize = srcLayer.layer.XSize
    #set pixelsiae:
    pixelSize = 0.10
    minX = -180
    maxY = 90
    gt = (minX, pixelSize, 0, maxY, 0, -pixelSize)
    spatialRef = MjProj()
    spatialRef.SetFromEPSG(4326)
    spatialRef.SetGeoTrans(gt)
    
    tarDS = RasterDataSource()
    
    tarLayer = RasterLayer()
    tarLayer.cols = XSize
    tarLayer.lins = YSize
    tarLayer.geotrans = gt
    tarLayer.projection = spatialRef.proj_cs.ExportToWkt()
    
    #Rotate
    BAND = np.rot90(srcLayer.NPBAND)

    if comp.band in  ['imerg-3bv05b-gauge-weight','imerg-3bv05b-gauge-liquid']:
        BAND[BAND < 0] = 255
        BAND.astype(np.uint8)
    elif comp.band == 'imerg-3bv05b-quality':
        BAND = BAND*100
        BAND[BAND < 0] = -32768

    else:
        BAND = BAND*days.days*24 #hourly rainfall converted to monthly
        BAND.astype(np.int16)
        BAND[BAND < 0] = -32768
    
    tarLayer.BAND = BAND
    #tarLayer.BAND.astype(np.int16)
    tarLayer.SetSpatialRef(spatialRef)

    tarLayer.comp = comp
    
    tarDS.CreateGDALraster(dstFPN,tarLayer) 
    
    srcDS.CloseDS()
    tarDS.CloseDS()

def BinaryTranslate(inFPN,outFPN,celltype):
    #copied from mj_ancillary_v01
    #nC = 180*720
    mem_drv = gdal.GetDriverByName( 'MEM' )
    ncols, nlins = 360, 180
    if celltype == 'UInt8':
        dsOut = mem_drv.Create('', ncols, nlins, 1, gdal.GDT_Byte)
        valueArray = arr.array('B')
    elif celltype == 'Int16':
        dsOut = mem_drv.Create('', ncols, nlins, 1, gdal.GDT_Int16)
        valueArray = arr.array('h')
    elif celltype == 'UInt16':
        dsOut = mem_drv.Create('', ncols, nlins, 1, gdal.GDT_Int16)
        valueArray = arr.array('H')
    else:
        print ('Unknown datatype', celltype)
        sys.exit('Fix the datatype, either in db or in script')
    #Read the datafile
    datF = open(inFPN, 'rb')
    valueArray.fromfile(datF, ncols * nlins)
    datF.close()

    if celltype == 'UInt8':
        values = struct.pack('B'*len(valueArray), *valueArray)
    elif celltype == 'Int16':
        values = struct.pack('h'*len(valueArray), *valueArray)
    elif celltype == 'UInt16':
        values = struct.pack('H'*len(valueArray), *valueArray)
    else:
        sys.exit('something wrong with data type, check the script')
    dsOut.WriteRaster( 0, 0, ncols, nlins, values)

    # Output driver, as before
    driver = gdal.GetDriverByName ( "GTiff" )
    #The projection is laonlat, with 1 degree spatial resolution
    proj = osr.SpatialReference()  
    proj.SetWellKnownGeogCS( "EPSG:4326" )  
    dsOut.SetProjection(proj.ExportToWkt())  
    geotransform = (-180.0, 1.0, 0.0, 90.0, 0.0, -1.0)  
    dsOut.SetGeoTransform(geotransform)
    # Create a copy of the in memory dataset `reprojected_dataset`, and save it
    dst_ds = driver.CreateCopy( outFPN, dsOut, 0 ) 
    #Get the extension box and resolution of the dataset, i.e. the geotransform
    dst_ds = None        
    dsOut = None # Flush the dataset to disk
    
    
    

if __name__ == "__main__":
    
    pass