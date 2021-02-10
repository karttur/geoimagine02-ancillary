'''
Created on 23 feb. 2018

@author: thomasgumbricht
'''
__version__ = '0.9.0'

VERSION = tuple(int(x) for x in __version__.split('.'))

metadataD = { 'name':'ancillary', 
             'author':'Thomas Gumbricht', 'author_email':'thomas.gumbricht@gmail.com',
             'title':'Define, import, reformat and organize ancillary data.', 
             'label':'Processes for defining, importing, formating and organizing different types of spatial data. Both vectors and raster, as well as text based time-series data can be managed. Point data are usually imported as specimen data, or topodata.',
             'prerequisites':'The ancillary data must be locally available in a recognized (predefined) format.',
             'image':'avg-trmm-3b43v7-precip_3B43_trmm_2001-2016_A'
             }