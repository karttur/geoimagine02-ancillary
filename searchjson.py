'''
Created on 17 Mar 2021

@author: thomasgumbricht
'''

from sys import exit
import os

import json

from geoimagine.gis import kt_gis as ktgis
from geoimagine.zipper import UnZip

def JsonParams(jsonPath):
        '''
        '''

        # Opening JSON file
        f = open(jsonPath, "r")

        # returns JSON object
        return json.load(f)
    
def SetTileLocation():
    '''
    '''
    for lat in range(-90,91,1):
            
        if lat >= 0:
            
            if lat == 0:
                
                latdir = 'N00'
            
            if lat > 10:
                
                latdir = 'N%(lat)d' %{'lat':lat}
                
            else:
                
                latdir = 'N0%(lat)d' %{'lat':lat}
                
        else:
                                
            if lat <10:
                
                latdir = 'S%(lat)d' %{'lat':abs(lat)}
                
            else:
                
                latdir = 'S0%(lat)d' %{'lat':abs(lat)}
        
        for lon in range(-180,181,10):
            
            if lon >= 0:
                
                if lon == 0:
                    
                    londir = 'E000'
            
                if lon > 100:
                    
                    londir = 'E%(lon)d' %{'lon':lon}
                    
                elif lon > 10:
                    
                    londir = 'E0%(lon)d' %{'lon':lon}
                    
                else:
                    
                    londir = 'E00%(lon)d' %{'lon':lon}
                    
            else:
                                        
                if lon <-100:
                    
                    londir = 'N%(lon)d' %{'lon':abs(lon)}
                    
                elif lon < -10:
                    
                    londir = 'N0%(lon)d' %{'lon':abs(lon)}
            
                else:
                    
                    londir = 'N00%(lon)d' %{'lon':abs(lon)}
            
            #serverulr ='https://download.geoservice.dlr.de/TDM90/files/'
            
            # Set the name of the local html file that will contain the available data
            #htmlFN = '%s-%s.html' %(latdir,londir)
            
            # Set the local file name path
            #localFPN = os.path.join(self.localPath,htmlFN)
            
            # Define the complete url to the online data
            #url = os.path.join(self.pp.process.parameters.serverurl,self.onlineSource,'files',latdir,londir)
            
            #url ='https://download.geoservice.dlr.de/TDM90/files/N22/E020/'

            #print ('url',url)
            
            #print (localFPN)
            
            
def MakePolygon(minlon,maxlon,minlat,maxlat):
    '''
    '''
    
    if maxlon <= minlon:
        
        exit('maxlon <= minlon')
        
    if maxlat <= minlat:
        
        exit('maxlat <= minlat')
        
    ptL = [(minlon,maxlat),(maxlon,maxlat),(maxlon,minlat),(minlon,minlat)]
        

    return ktgis.ShapelyPolyGeom(ptL)

def SelectTiles(jsonpath,topdir,searchgeom):
    '''
    '''
    featureL = []
    
    featureCollection = JsonParams(jsonpath)
    
    for f in featureCollection['features']:
        
        if f['geometry']['type'] == 'Polygon':
                        
            ll,lr,ur,ul,ll = f['geometry']['coordinates'][0]
            
            minlon = ll[0]
            
            maxlon = lr[0]
            
            minlat = ll[1]
            
            maxlat = ul[1]
            
            if maxlon <= minlon:
        
                exit('tile maxlon <= minlon')
                
            if maxlat <= minlat:
                
                exit('tile maxlat <= minlat')
            
            ptL = [(minlon,maxlat),(maxlon,maxlat),(maxlon,minlat),(minlon,maxlat)]
    
            tilegeom = ktgis.ShapelyPolyGeom(ptL)
            
            tileId = f['properties']['id']
            
            if tilegeom.shapelyGeom.intersects(searchgeom.shapelyGeom):
                                
                url = f['properties']['Download']
                
                tileId = f['properties']['id']
                
                fn = f['properties']['filename']
                
                dstFPN = os.path.join(topdir,'ZIP',fn)
                
                featureL.append({'url':url,'tileId':tileId,'fn':fn,'dstFPN':dstFPN})
                
    return featureL
           
def UnZipJsonTandemX(volume,params):
    '''
    '''
    datadir = params.datadir
    jsonpath = params.path
    minlon = params.minlon
    maxlon = params.maxlon
    minlat = params.minlat
    maxlat = params.maxlat
    
    topdir = os.path.join('/Volumes',volume,datadir)
    
    demdir = os.path.join(topdir,'DEM')
    
    if not os.path.exists(demdir):
        
        os.makedirs(demdir)
        
    searchgeom = MakePolygon(minlon,maxlon,minlat,maxlat)
    
    featureL = SelectTiles(jsonpath,topdir,searchgeom)
    
    for feature in featureL:
        
        demFN = feature['fn'].replace('.zip','_DEM.tif')
        
        demFPN = os.path.join(topdir,demdir,demFN)
        
        if os.path.exists(feature['dstFPN']) and not os.path.exists(demFPN):
            
            print ('unzip',feature['dstFPN'],demFPN)
            
            UnZip(feature['dstFPN'], demdir, demFN)
    
def SearchJsonTandemX(volume,params):
    ''' Search GeoJson for tandemX tiles to download
    '''
    
    datadir = params.datadir
    jsonpath = params.path
    minlon = params.minlon
    maxlon = params.maxlon
    minlat = params.minlat
    maxlat = params.maxlat
    user = params.username 
    pswd = params.password
    
    topdir = os.path.join('/Volumes',volume,datadir)
    
    searchgeom = MakePolygon(minlon,maxlon,minlat,maxlat)
                    
    # Loop through all features
    featureL = SelectTiles(jsonpath,topdir,searchgeom)
    
    # Set filename to the search boundary
    listFn = 'W%(minlon)d_E%(maxlon)d_S%(minlat)d_N%(maxlat)d.txt' %{'minlon':minlon,'maxlon':maxlon,'minlat':minlat,'maxlat':maxlat}
    
    fpn = os.path.join(topdir,listFn)
    
    if not os.path.exists(topdir):
        
        os.makedirs(topdir)
        
    file = open(fpn,'w')
    
    for feature in featureL:
              
        if not os.path.exists(feature['dstFPN']):
            
            infostr = 'Adding: %s' %(feature['tileId'])
            
            writestr = '%s\n' %(feature['url'])
            
            file.write(writestr)
            
        else:
            
            infostr = 'Already done: %s' %(feature['tileId'])
            
        print (infostr)
                      
    file.close()
    
    infostr = "Download file: %s\n\n" %(fpn)
    
    infostr += "cd %s\n" %(topdir)
    
    infostr += "# curl $(printf ' -O %(fn)s' $(<TDM90mDEM-url-list.txt)) -u 'username:password'\n" %{'fn':listFn}
    
    infostr += "aria2c -i %(fn)s --http-user '%(user)s' --http-passwd '%(pswd)s'\n" %{'fn':listFn,'user':user,'pswd':pswd}
    
    infostr += 'for i in *.zip; do mv "$i" "ZIP/"$i""; done'
    
    print (infostr)
        
if __name__ == "__main__":

      
    datadir = '/Volumes/Ancillary/RAWAUXILIARY/TDM90'
    jsonpath = '/Volumes/Ancillary/DOWNLOADS/tdm90/tandem-X_grid.json'
    minlon = 9
    maxlon = 25
    minlat = 54
    maxlat = 70
    user = 'thomas.gumbricht@gmail.com' 
    pswd = 'co5-l4G-67a-tIR'
    SearchJsonTandemX(datadir, jsonpath, minlon, maxlon, minlat, maxlat, user, pswd)
    
    