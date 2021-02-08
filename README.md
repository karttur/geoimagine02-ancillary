# geoimagine-ancillary

Karttur Geoimagine ancillary data python project

## Introduction

Karttur's GeoImagine Framework is an attempt for semi-automated processing of spatial data. 
The ancillary package contains the processing for defining, downloading and organizing ancillary 
datasets and datalayers. In the Framework ancillary should be regarded as all data except satellite images,
and time--series data derived from satellite date.

The package contains 4 modules:


- \_\_init.py\_\_
- ancillary.py
- dataprep.py
- version.py

### ancillary.py

#### GeoImagine dependencies

- geoimagine.kartturmain
- geoimagine.support.karttur_dt
- geoimagine.gis.gis

#### Classes

- AncilComposition(Composition)
- AncillaryLayer(RegionLayer)
- ProcessAncillary
