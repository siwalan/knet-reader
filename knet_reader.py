import struct
import binascii
import numpy as np
import os
import json

##### HELPER FUNCTION ######

def BCDLatToFloat(BCDLat):
    BCDLat = BCDLat.decode('ASCII')
    BCDLat = BCDLat.lower()
    DecimalReduction = 0
    for x in range(len(BCDLat)-1,0,-1):
        if BCDLat[x] == "e":
            DecimalReduction += 1
    ZeroPadding = len(BCDLat) - len(BCDLat.lstrip("0"))
    NumberOfDigits = 8 - DecimalReduction
    SignificantFigures = 5 - DecimalReduction
    
    return round(int(BCDLat[ZeroPadding:NumberOfDigits]) * 10**-SignificantFigures,SignificantFigures)

def BCDLongToFloat(BCDLong):
    BCDLong = BCDLong.decode('ASCII')
    BCDLong = BCDLong.lower()
    DecimalReduction = 0
    for x in range(len(BCDLong)-1,0,-1):
        if BCDLong[x] == "e":
            DecimalReduction += 1
    ZeroPadding = len(BCDLong) - len(BCDLong.lstrip("0"))
    NumberOfDigits = 8 - DecimalReduction
    SignificantFigures = 5 - DecimalReduction
    
    return round(int(BCDLong[ZeroPadding:NumberOfDigits]) * 10**-SignificantFigures, SignificantFigures)

def BCDElevationToFloat(BCDElevation):
    BCDElevation = BCDElevation.decode('ASCII')
    BCDElevation = BCDElevation.lower()
    DecimalReduction = 0
    for x in range(len(BCDElevation)-1,0,-1):
        if BCDElevation[x] == "e":
            DecimalReduction += 1
    if BCDElevation[0] == 'd':
        Sign = -1
    else:
        Sign = 1
    ZeroPadding = len(BCDElevation[1:]) - len(BCDElevation[1:].lstrip("0"))
    NumberOfDigits = 8 - DecimalReduction 
    SignificantFigures = 2 - DecimalReduction
    
    return round(Sign * int(BCDElevation[ZeroPadding:NumberOfDigits]) * 10**-SignificantFigures,SignificantFigures)

def BCDEQDepth(BCDElevation):
    BCDElevation = BCDElevation.decode('ASCII')
    BCDElevation = BCDElevation.lower()
    DecimalReduction = 0
    for x in range(len(BCDElevation)-1,0,-1):
        if BCDElevation[x] == "e":
            DecimalReduction += 1
    if BCDElevation[0] == 'd':
        Sign = -1
    else:
        Sign = 1
    ZeroPadding = len(BCDElevation[1:]) - len(BCDElevation[1:].lstrip("0"))
    NumberOfDigits = 8 - DecimalReduction 
    SignificantFigures = 3 - DecimalReduction
    
    return round(Sign * int(BCDElevation[ZeroPadding:NumberOfDigits]) * 10**-SignificantFigures,SignificantFigures)


def BCDEQScale(BCDEQScale):
    BCDEQScale = BCDEQScale.decode('ASCII')
    BCDEQScale = BCDEQScale.lower()
    DecimalReduction = 0
    for x in range(len(BCDEQScale)-1,0,-1):
        if BCDEQScale[x] == "e":
            DecimalReduction += 1
    if BCDEQScale[0] == 'd':
        Sign = -1
    else:
        Sign = 1
    NumberOfDigits = 2 - DecimalReduction 
    SignificantFigures = 1 - DecimalReduction
    
    return round(Sign * int(BCDEQScale[0:NumberOfDigits]) * 10**-SignificantFigures,SignificantFigures)


def HexToBinary(hex_string):
    decimal_value = int(hex_string, 16)
    
    if 0 <= decimal_value < 2**12:
        return decimal_value
    else:
        raise ValueError("INVALID VALUE")

def parse_knet_data(filepath):

    if os.path.splitext(filepath)[1] == ".kwin":
        with open(filepath, mode='rb') as file: # b is important -> binary
            fileContent = file.read()

        GM_DIRECTION = ["NS","EW","UD"]
        GM_TYPE = 0
        GROUND_MOTION_ARRAY = np.zeros((3,1))
        DIRECTION_TIME_SERIES = [0,0,0]

        ## File Sanity Check - Strong WIN32 Header Block
        CurrentBinaryStart = 0
        assert struct.unpack_from('>BBBB', fileContent, CurrentBinaryStart) == (10,2,0,0)
        CurrentBinaryStart += 4
        ## Information Block 
        ## Information Block Header
        assert struct.unpack_from('>BBBB', fileContent, CurrentBinaryStart)  == (12,0,0,0)
        CurrentBinaryStart += 4
        OrganizationID, ObservationNetwork, = struct.unpack_from('>BB', fileContent, CurrentBinaryStart) 
        CurrentBinaryStart += 2
        SeismographNumber = struct.unpack_from('>H', fileContent, CurrentBinaryStart) 
        CurrentBinaryStart += 2
        DataBlockLength = struct.unpack_from('>I', fileContent, CurrentBinaryStart) 
        CurrentBinaryStart += 4

        # Information data block (1) Observation point information (three-component surface observation point)
        InformationType  = struct.unpack_from('>H', fileContent, CurrentBinaryStart) 
        CurrentBinaryStart += 2
        InformationDataSize	= struct.unpack_from('>H', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 2
        # Observation point information
        LatitudeHex  = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+4]) 
        StationLatitude = BCDLatToFloat(LatitudeHex)
        CurrentBinaryStart += 4
        LongitudeHex	= binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+4]) 
        StationLongitude = BCDLongToFloat(LongitudeHex)
        CurrentBinaryStart += 4
        ElevationHex	= binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+4])
        StationElevation = BCDElevationToFloat(ElevationHex) 
        CurrentBinaryStart += 4
        ObservationPointCode = str((fileContent[CurrentBinaryStart:CurrentBinaryStart+12]).decode('ascii').rstrip('\x00')) 
        CurrentBinaryStart += 12
        DataStartTime = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+8])  
        CurrentBinaryStart += 8
        MeasurementTimeLength = struct.unpack_from('>I', fileContent, CurrentBinaryStart) 
        CurrentBinaryStart += 4
        LastTimeCalibration = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+8])  
        CurrentBinaryStart += 8
        CalibrationMethod = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        GeodeticSystem = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        SeismometerModelCode = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+2])  
        CurrentBinaryStart += 2
        SamplingRate = struct.unpack_from('>H', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 2
        NumberOfComponents = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        RelocationFlag = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1

        #Information about the north-south component (NS)
        NS_ORG_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        NS_OBS_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        NS_CHN_ID = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+2])
        CurrentBinaryStart += 2
        NS_SCALE_FACTOR_NUMERATOR = struct.unpack_from('>h', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 2
        NS_GAIN = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+1])
        CurrentBinaryStart += 1
        NS_UNIT = struct.unpack_from('>B', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 1
        NS_SCALE_FACTOR_DENOMINATOR = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4
        NS_OFFSET = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4
        NS_MEASUREMENT_RANGE = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4

        #Information about the north-south component (EW)
        EW_ORG_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        EW_OBS_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        EW_CHN_ID = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+2])
        CurrentBinaryStart += 2
        EW_SCALE_FACTOR_NUMERATOR = struct.unpack_from('>h', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 2
        EW_GAIN = struct.unpack_from('>B', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 1
        EW_UNIT = struct.unpack_from('>B', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 1
        EW_SCALE_FACTOR_DENOMINATOR = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4
        EW_OFFSET = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4
        EW_MEASUREMENT_RANGE = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4

        #Information about the north-south component (UD)
        UD_ORG_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        UD_OBS_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        UD_CHN_ID = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+2])
        CurrentBinaryStart += 2
        UD_SCALE_FACTOR_NUMERATOR = struct.unpack_from('>h', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 2
        UD_GAIN = struct.unpack_from('>B', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 1
        UD_UNIT = struct.unpack_from('>B', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 1
        UD_SCALE_FACTOR_DENOMINATOR = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4
        UD_OFFSET = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4
        UD_MEASUREMENT_RANGE = struct.unpack_from('>i', fileContent, CurrentBinaryStart)[0]
        CurrentBinaryStart += 4

        #Information data block (2) Earthquake information *This information data block is not included in the case of immediate release data
        EQ_INFORMATION_TYPE = struct.unpack_from('>h', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 2
        EQ_INFORMATION_SIZE = struct.unpack_from('>h', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 2

        EQ_OT = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+8])  
        CurrentBinaryStart += 8
        EQ_LatitudeHex  = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+4]) 
        EQ_Latitude = BCDLatToFloat(EQ_LatitudeHex)
        CurrentBinaryStart += 4
        EQ_LongitudeHex	= binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+4]) 
        EQ_Longitude = BCDLongToFloat(EQ_LongitudeHex)
        CurrentBinaryStart += 4
        EQ_DepthHex	= binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+4]) 
        EQ_Depth = BCDEQDepth(EQ_DepthHex)
        CurrentBinaryStart += 4
        EQ_SCALEHex = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+1]) 
        EQ_Scale = BCDEQScale(EQ_SCALEHex)
        CurrentBinaryStart += 1
        EQ_GeodeticSystem = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        EQ_EpicenterType = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1
        EQ_Reservation = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
        CurrentBinaryStart += 1

        GM_DIRECTION = ["NS","EW","UD"]
        GM_TYPE = 0
        GROUND_MOTION_ARRAY = np.zeros((3,1))
        DIRECTION_TIME_SERIES = [0,0,0]
        CHECK = 0
        while True:
            First_Sampling_time = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+8])  
            if (First_Sampling_time).decode("ASCII") == '':
                break
            CurrentBinaryStart += 8
            Frame_Duration = struct.unpack_from('>i', fileContent, CurrentBinaryStart) 
            CurrentBinaryStart += 4
            Data_Block_Length = struct.unpack_from('>i', fileContent, CurrentBinaryStart) 
            CurrentBinaryStart += 4
            NUMPY_INIT = 0 
            while GM_TYPE <= 2:
                ### Change to Assert for Sanity Check
                DIR_ORG_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
                CurrentBinaryStart += 1
                DIR_OBS_ID = struct.unpack_from('>B', fileContent, CurrentBinaryStart)
                CurrentBinaryStart += 1
                NS_CHN_ID = struct.unpack_from('>H', fileContent, CurrentBinaryStart)
                CurrentBinaryStart += 2
                ### Compressed Data Reading
                SAMPLE_DATA = binascii.hexlify(fileContent[CurrentBinaryStart:CurrentBinaryStart+2])
                SAMPLE_SIZE_TYPE = SAMPLE_DATA[0:1].decode('ascii')
                NUMBER_OF_SAMPLE = SAMPLE_DATA[1:].decode('ascii')
                NUMBER_OF_SAMPLE = hex_to_12bit_unsigned(NUMBER_OF_SAMPLE)
                CurrentBinaryStart += 2

                if NUMPY_INIT == 0:
                    GROUND_MOTION_ARRAY = np.concatenate((GROUND_MOTION_ARRAY,np.zeros((3,NUMBER_OF_SAMPLE))),axis=1)
                    NUMPY_INIT = 1
                if SAMPLE_SIZE_TYPE == '2':
                    DifferenceData = 2
                elif SAMPLE_SIZE_TYPE == '1':
                    DifferenceData = 1
                else:
                    print("ERROR")
                for x in range(NUMBER_OF_SAMPLE):
                    if x == 0:       
                        FIRST_SAMPLE_VALUE = struct.unpack_from('>i', fileContent, CurrentBinaryStart)
                        CurrentBinaryStart += 4
                        GROUND_MOTION_ARRAY[GM_TYPE,DIRECTION_TIME_SERIES[GM_TYPE]] = FIRST_SAMPLE_VALUE[0]
                        CURRENT_VALUE = FIRST_SAMPLE_VALUE[0]
                        DIRECTION_TIME_SERIES[GM_TYPE] += 1
                    else:
                        if DifferenceData == 2:
                            DiffValue = struct.unpack_from('>h', fileContent, CurrentBinaryStart)
                        elif DifferenceData == 1:
                            DiffValue = struct.unpack_from('>b', fileContent, CurrentBinaryStart)
        
                        CurrentBinaryStart += DifferenceData
                        CURRENT_VALUE = CURRENT_VALUE + DiffValue[0]
                        GROUND_MOTION_ARRAY[GM_TYPE,DIRECTION_TIME_SERIES[GM_TYPE]] = CURRENT_VALUE
                        DIRECTION_TIME_SERIES[GM_TYPE] += 1
                GM_TYPE += 1
            GM_TYPE = 0

        GROUND_MOTION_ARRAY[0] = GROUND_MOTION_ARRAY[0] - NS_OFFSET
        GROUND_MOTION_ARRAY[0] = GROUND_MOTION_ARRAY[0] *  (NS_SCALE_FACTOR_NUMERATOR/NS_SCALE_FACTOR_DENOMINATOR) 

        GROUND_MOTION_ARRAY[1] = GROUND_MOTION_ARRAY[1] - EW_OFFSET
        GROUND_MOTION_ARRAY[1] = GROUND_MOTION_ARRAY[1] *  (EW_SCALE_FACTOR_NUMERATOR/EW_SCALE_FACTOR_DENOMINATOR) 

        GROUND_MOTION_ARRAY[2] = GROUND_MOTION_ARRAY[2] - EW_OFFSET
        GROUND_MOTION_ARRAY[2] = GROUND_MOTION_ARRAY[2] *  (EW_SCALE_FACTOR_NUMERATOR/EW_SCALE_FACTOR_DENOMINATOR)

        GROUND_MOTION_ARRAY = GROUND_MOTION_ARRAY[:,:-1]

        metadata = {}
        metadata["Earthquake"] = {}
        metadata["Earthquake"]["EQScale"] = EQ_Scale
        metadata["Earthquake"]["Latitude"] = EQ_Latitude
        metadata["Earthquake"]["Longitude"] = EQ_Longitude
        metadata["Earthquake"]["Depth"] = EQ_Depth
        metadata["StationData"] = {}
        metadata["StationData"]["StationID"] = ObservationPointCode
        metadata["StationData"]["Latitude"] = StationLatitude
        metadata["StationData"]["Longitude"] = StationLongitude
        metadata["StationData"]["Elevation"] = StationElevation
        
        return GROUND_MOTION_ARRAY, metadata