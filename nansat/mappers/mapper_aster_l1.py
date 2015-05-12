# Name:        mapper_modisL1
# Purpose:     Mapping for MODIS-L1 data
# Authors:      Anton Korosov
# Licence:      This file is part of NANSAT. You can redistribute it or modify
#               under the terms of GNU General Public License, v.3
#               http://www.gnu.org/licenses/gpl-3.0.html
from dateutil.parser import parse
import warnings

from nansat.tools import gdal, ogr, WrongMapperError
from nansat.vrt import VRT


class Mapper(VRT):
    ''' VRT with mapping of WKV for MODIS Level 1 (QKM, HKM, 1KM) '''

    def __init__(self, fileName, gdalDataset, gdalMetadata, emrange='VNIR', **kwargs):
        ''' Create MODIS_L1 VRT '''
        # check mapper
        if gdalMetadata.get('INSTRUMENTSHORTNAME', '') != 'ASTER':
            raise WrongMapperError
        if gdalMetadata.get('SHORTNAME', '') != 'ASTL1B':
            raise WrongMapperError


        # set up metadict for data with various resolution
        subDSString = 'HDF4_EOS:EOS_SWATH:"%s":%s:%s'
        metaDictVNIR = [
        {'src': {'SourceFilename': subDSString % (fileName, 'VNIR_Swath', 'ImageData1' )}, 'dst': {'wavelength': '560'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'VNIR_Swath', 'ImageData2' )}, 'dst': {'wavelength': '660'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'VNIR_Swath', 'ImageData3N')}, 'dst': {'wavelength': '820'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'VNIR_Swath', 'ImageData3B')}, 'dst': {'wavelength': '820'}},
        ]

        metaDictSWIR = [
        {'src': {'SourceFilename': subDSString % (fileName, 'SWIR_Swath', 'ImageData4')}, 'dst': {'wavelength': '1650'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'SWIR_Swath', 'ImageData5')}, 'dst': {'wavelength': '2165'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'SWIR_Swath', 'ImageData6')}, 'dst': {'wavelength': '2205'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'SWIR_Swath', 'ImageData7')}, 'dst': {'wavelength': '2260'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'SWIR_Swath', 'ImageData8')}, 'dst': {'wavelength': '2330'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'SWIR_Swath', 'ImageData9')}, 'dst': {'wavelength': '2395'}},
        ]

        metaDictTIR = [
        {'src': {'SourceFilename': subDSString % (fileName, 'TIR_Swath',  'ImageData10')}, 'dst': {'wavelength': '8300'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'TIR_Swath',  'ImageData11')}, 'dst': {'wavelength': '8650'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'TIR_Swath',  'ImageData12')}, 'dst': {'wavelength': '9100'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'TIR_Swath',  'ImageData13')}, 'dst': {'wavelength': '10600'}},
        {'src': {'SourceFilename': subDSString % (fileName, 'TIR_Swath',  'ImageData14')}, 'dst': {'wavelength': '11300'}},
        ]


        # select appropriate metaDict based on <emrange> parameter
        metaDict = {'VNIR': metaDictVNIR,
                    'SWIR': metaDictSWIR,
                    'TIR': metaDictTIR,
                    }[emrange]

        # get 1st EOS subdataset and parse to VRT.__init__()
        # for retrieving geo-metadata
        try:
            gdalSubDataset0 = gdal.Open(metaDict[0]['src']['SourceFilename'])
        except (AttributeError, IndexError):
            raise WrongMapperError

        # create empty VRT dataset with geolocation only
        VRT.__init__(self, gdalSubDataset0)

        # add source band, wkv and suffix
        for metaEntry in metaDict:
            metaEntry['src']['SourceBand'] = 1
            metaEntry['dst']['wkv'] = 'toa_outgoing_spectral_radiance'
            metaEntry['dst']['suffix'] = metaEntry['dst']['wavelength']

            if 'ImageData3N' in metaEntry['src']['SourceFilename']:
                metaEntry['dst']['suffix'] += 'N'

            if 'ImageData3B' in metaEntry['src']['SourceFilename']:
                metaEntry['dst']['suffix'] += 'B'

        """
        # read all scales/offsets
        rScales = {}
        rOffsets = {}
        for sf in metaDictSF:
            dsName = subDsString % (fileName, sf)
            ds = gdal.Open(dsName)
            rScales[dsName] = map(float,
                                  ds.GetMetadataItem('radiance_scales').
                                  split(','))
            rOffsets[dsName] = map(float,
                                   ds.GetMetadataItem('radiance_offsets').
                                   split(','))
            self.logger.debug('radiance_scales: %s' % str(rScales))

        # add 'band_name' to 'parameters'
        for bandDict in metaDict:
            SourceFilename = bandDict['src']['SourceFilename']
            SourceBand = bandDict['src']['SourceBand']
            bandDict['dst']['suffix'] = bandDict['dst']['wavelength']
            scale = rScales[SourceFilename][SourceBand-1]
            offset = rOffsets[SourceFilename][SourceBand-1]
            self.logger.debug('band, scale, offset: %s_%d %s %s' %
                              (SourceFilename, SourceBand, scale, offset))
            bandDict['src']['ScaleRatio'] = scale
            bandDict['src']['ScaleOffset'] = offset
        """

        # add bands with metadata and corresponding values to the empty VRT
        self._create_bands(metaDict)

        """
        productDate = gdalMetadata["RANGEBEGINNINGDATE"]
        productTime = gdalMetadata["RANGEENDINGTIME"]
        self._set_time(parse(productDate+' '+productTime))
        """
        self.remove_geolocationArray()
