import struct
import binascii
import numpy as np
import os
import json
from datetime import datetime, timedelta
from bitstring import BitStream

##### HELPER FUNCTION ######    
def BCDToFloat(BCD,NumDigit=8, SigDigit=5):
    if not isinstance(BCD,str):
        BCD = BCD.decode("ASCII")
    BCD = BCD.lower()
    DecimalReduction = 0
    for x in range(len(BCD)-1,0,-1):
        if BCD[x] == 'e':
            DecimalReduction += 1
    
    Sign = 1
    StartLStrip=0
    if not BCD[0].isdigit():
        StartLStrip=1
        if BCD[0] == 'd':
            Sign = -1   
    
    ZeroPadding = len(BCD) - len(BCD[StartLStrip:].lstrip("0"))
    NumberOfDigits = NumDigit - DecimalReduction
    SignificantFigures = SigDigit - DecimalReduction
    return round(int(BCD[(ZeroPadding):NumberOfDigits]) * 10**-SignificantFigures, SignificantFigures)

def ParseTime(time_str):
    # Splitting the time string into parts
    year = int(time_str[0:4])
    month = int(time_str[4:6])
    day = int(time_str[6:8])
    hour = int(time_str[8:10])
    minute = int(time_str[10:12])
    second = int(time_str[12:14])
    tenths_of_second = int(time_str[14:16])

    # Create a datetime object
    dt = datetime(year, month, day, hour, minute, second)
    
    # Add tenths of a second (convert tenths to microseconds for datetime)
    microsecond = tenths_of_second * 100000  # 1 tenth of a second is 100,000 microseconds
    dt += timedelta(microseconds=microsecond)

    return dt
    
def HexToBinary(hex_string):
    decimal_value = int(hex_string, 16)
    
    if 0 <= decimal_value < 2**12:
        return decimal_value
    else:
        raise ValueError("INVALID VALUE")

def KNETUnitHandler(UnitBytes):
    UnitBytes = UnitBytes[0]
    NegativePowerOf = (UnitBytes >> 4) & 0x0F
    Unit = UnitBytes & 0x0F

    if Unit == 1:
        Unit = "m"
    elif Unit == 2:
        Unit = "m/s"
    elif Unit == 3:
        Unit = "m/s^2"
    else:
        Unit = "Undefined"

    return NegativePowerOf, Unit



##### MAIN FUNCTION ######

def parse_knet_data(filepath,CONVERT_RESULT=False):

    if os.path.splitext(filepath)[1] == ".kwin":
        with open(filepath, mode='rb') as file: # b is important -> binary
            fileContent = file.read()

        ## WIN32 Header Block
        Pointer = 0
        assert struct.unpack_from('>BBBB', fileContent, Pointer) == (10,2,0,0)
        Pointer += 4
        
        ## Information Block 
        
        ## Information Block Header
        assert struct.unpack_from('>BBBB', fileContent, Pointer)  == (12,0,0,0)
        Pointer += 4
        
        OrganizationID, ObservationNetwork, SeismographNumber, DataBlockLength = struct.unpack_from('>BBHI', fileContent, Pointer) 
        Pointer += 8
        
        # Information data block (1) Observation point information (three-component surface observation point)
        InformationType, InformationDataSize  = struct.unpack_from('>HH', fileContent, Pointer) 
        Pointer += 4
        
        # Observation point information
        LatitudeHex, LongitudeHex  = binascii.hexlify(fileContent[Pointer:Pointer+4]), binascii.hexlify(fileContent[Pointer+4:Pointer+8])
        StationLatitude, StationLongitude = BCDToFloat(LatitudeHex), BCDToFloat(LongitudeHex)
        Pointer += 8
        
        ElevationHex, Pointer	= binascii.hexlify(fileContent[Pointer:Pointer+4]),Pointer + 4
        StationElevation = BCDToFloat(ElevationHex,8,2) 
        
        ObservationPointCode, Pointer = str((fileContent[Pointer:Pointer+12]).decode('ascii').rstrip('\x00')), Pointer + 12
        
        DataStartTime, Pointer = binascii.hexlify(fileContent[Pointer:Pointer+8]),  Pointer + 8
        MeasurementTimeLength = struct.unpack_from('>I', fileContent, Pointer) 
        Pointer += 4
        LastTimeCalibration, Pointer = binascii.hexlify(fileContent[Pointer:Pointer+8]),Pointer + 8
        
        CalibrationMethod, GeodeticSystem = struct.unpack_from('>BB', fileContent, Pointer)
        Pointer += 2
        SeismometerModelCode = binascii.hexlify(fileContent[Pointer:Pointer+2])  
        Pointer += 2
        SamplingRate,NumberOfComponents,RelocationFlag = struct.unpack_from('>HBB', fileContent, Pointer)
        Pointer += 4
        
        
        #Information about the north-south component (NS)
        NS_ORG_ID, NS_OBS_ID = struct.unpack_from('>BB', fileContent, Pointer)
        Pointer += 2
        
        NS_CHN_ID, NS_SCALE_FACTOR_NUMERATOR,NS_GAIN = struct.unpack_from('>HhB', fileContent, Pointer)
        Pointer += 5
        NS_UNIT = fileContent[Pointer:Pointer+1]
        Pointer += 1
        NS_UNIT_POWER, NS_UNIT_TYPE = KNETUnitHandler(NS_UNIT)
        NS_SCALE_FACTOR_DENOMINATOR,NS_OFFSET,NS_MEASUREMENT_RANGE = struct.unpack_from('>iii', fileContent, Pointer)
        Pointer += 12
        
        #Information about the north-south component (EW)
        UD_ORG_ID, UD_OBS_ID = struct.unpack_from('>BB', fileContent, Pointer)
        Pointer += 2
        
        EW_CHN_ID, EW_SCALE_FACTOR_NUMERATOR,EW_GAIN = struct.unpack_from('>HhB', fileContent, Pointer)
        Pointer += 5
        EW_UNIT = fileContent[Pointer:Pointer+1]
        Pointer += 1
        EW_UNIT_POWER, EW_UNIT_TYPE = KNETUnitHandler(EW_UNIT)
        EW_SCALE_FACTOR_DENOMINATOR,EW_OFFSET,EW_MEASUREMENT_RANGE = struct.unpack_from('>iii', fileContent, Pointer)
        Pointer += 12
        
        #Information about the north-south component (UD)
        UD_ORG_ID, UD_OBS_ID = struct.unpack_from('>BB', fileContent, Pointer)
        Pointer += 2
        
        UD_CHN_ID, UD_SCALE_FACTOR_NUMERATOR,UD_GAIN = struct.unpack_from('>HhB', fileContent, Pointer)
        Pointer += 5
        UD_UNIT = fileContent[Pointer:Pointer+1]
        Pointer += 1
        UD_UNIT_POWER, UD_UNIT_TYPE = KNETUnitHandler(UD_UNIT)
        UD_SCALE_FACTOR_DENOMINATOR,UD_OFFSET,UD_MEASUREMENT_RANGE = struct.unpack_from('>iii', fileContent, Pointer)
        Pointer += 12
        
        if DataBlockLength == 144:
            EQ_INFORMATION_TYPE = struct.unpack_from('>h', fileContent, Pointer)
            Pointer += 2
            EQ_INFORMATION_SIZE = struct.unpack_from('>h', fileContent, Pointer)
            Pointer += 2
            
            EQ_OT = binascii.hexlify(fileContent[Pointer:Pointer+8])  
            EQOT = ParseTime(EQ_OT.decode('ASCII'))
            Pointer += 8
            EQ_LatitudeHex  = binascii.hexlify(fileContent[Pointer:Pointer+4]) 
            EQ_Latitude = BCDToFloat(EQ_LatitudeHex)
            Pointer += 4
            EQ_LongitudeHex	= binascii.hexlify(fileContent[Pointer:Pointer+4]) 
            EQ_Longitude = BCDToFloat(EQ_LongitudeHex)
            Pointer += 4
            EQ_DepthHex	= binascii.hexlify(fileContent[Pointer:Pointer+4]) 
            EQ_Depth = BCDToFloat(EQ_DepthHex,8,3)
            Pointer += 4
            EQ_SCALEHex = binascii.hexlify(fileContent[Pointer:Pointer+1]) 
            EQ_Scale = BCDToFloat(EQ_SCALEHex,2,1)
            Pointer += 1
            EQ_GeodeticSystem, EQ_EpicenterType, EQ_Reservation = struct.unpack_from('>BBB', fileContent, Pointer)
            Pointer += 3
        
        GM_DIRECTION = ["NS","EW","UD"]
        GM_TYPE = 0
        GROUND_MOTION_ARRAY = np.zeros((3,1))
        DIRECTION_TIME_SERIES = [0,0,0]
        CHECK = 0
        while True:
            First_Sampling_time = binascii.hexlify(fileContent[Pointer:Pointer+8])  
            if (First_Sampling_time).decode("ASCII") == '':
                break
            Pointer += 8
            Frame_Duration = struct.unpack_from('>i', fileContent, Pointer) 
            Pointer += 4
            Data_Block_Length = struct.unpack_from('>i', fileContent, Pointer) 
            Pointer += 4
            NUMPY_INIT = 0 
            while GM_TYPE <= 2:
                ### Change to Assert for Sanity Check
                DIR_ORG_ID = struct.unpack_from('>B', fileContent, Pointer)
                Pointer += 1
                DIR_OBS_ID = struct.unpack_from('>B', fileContent, Pointer)
                Pointer += 1
                NS_CHN_ID = struct.unpack_from('>H', fileContent, Pointer)
                Pointer += 2
                ### Compressed Data Reading
                SAMPLE_DATA = (fileContent[Pointer:Pointer+2])
                bit_stream = BitStream(SAMPLE_DATA)
                SAMPLE_SIZE_TYPE = bit_stream.read('uint:4')
                NUMBER_OF_SAMPLE = bit_stream.read('uint:12')

                Pointer += 2

                if NUMPY_INIT == 0:
                    GROUND_MOTION_ARRAY = np.concatenate((GROUND_MOTION_ARRAY,np.zeros((3,NUMBER_OF_SAMPLE))),axis=1)
                    NUMPY_INIT = 1
                    
                if SAMPLE_SIZE_TYPE == 4:
                    DifferenceData = 4
                elif SAMPLE_SIZE_TYPE == 3:
                    DifferenceData = 3
                elif SAMPLE_SIZE_TYPE == 2:
                    DifferenceData = 2
                elif SAMPLE_SIZE_TYPE == 1:
                    DifferenceData = 1
                x = 0
                while x < (NUMBER_OF_SAMPLE):
                    if x == 0:       
                        FIRST_SAMPLE_VALUE = struct.unpack_from('>i', fileContent, Pointer)
                        Pointer += 4
                        GROUND_MOTION_ARRAY[GM_TYPE,DIRECTION_TIME_SERIES[GM_TYPE]] = FIRST_SAMPLE_VALUE[0]
                        CURRENT_VALUE = FIRST_SAMPLE_VALUE[0]
                        DIRECTION_TIME_SERIES[GM_TYPE] += 1
                        x += 1
                    else:
                        if SAMPLE_SIZE_TYPE != 0:
                            DiffValue = int.from_bytes(fileContent[Pointer:Pointer+DifferenceData],'big',signed=True)    
                            Pointer += DifferenceData
                            CURRENT_VALUE = CURRENT_VALUE + DiffValue
                            GROUND_MOTION_ARRAY[GM_TYPE,DIRECTION_TIME_SERIES[GM_TYPE]] = CURRENT_VALUE
                            DIRECTION_TIME_SERIES[GM_TYPE] += 1
                            x += 1
                        else:
                            byte = fileContent[Pointer:Pointer+1]
                            Pointer += 1	
                            bit_stream = BitStream(byte)
                            high_nibble = bit_stream.read('int:4')
                            low_nibble = bit_stream.read('int:4')
                            CURRENT_VALUE = CURRENT_VALUE + high_nibble
                            GROUND_MOTION_ARRAY[GM_TYPE,DIRECTION_TIME_SERIES[GM_TYPE]] = CURRENT_VALUE
                            DIRECTION_TIME_SERIES[GM_TYPE] += 1
                            x += 1
                            if  x < NUMBER_OF_SAMPLE and NUMBER_OF_SAMPLE % 2 == 0:
                                CURRENT_VALUE = CURRENT_VALUE + low_nibble
                                GROUND_MOTION_ARRAY[GM_TYPE,DIRECTION_TIME_SERIES[GM_TYPE]] = CURRENT_VALUE
                                DIRECTION_TIME_SERIES[GM_TYPE] += 1
                            x += 1

                GM_TYPE += 1
            GM_TYPE = 0
        
        if CONVERT_RESULT:
            GROUND_MOTION_ARRAY[0] = GROUND_MOTION_ARRAY[0] - NS_OFFSET
            GROUND_MOTION_ARRAY[0] = GROUND_MOTION_ARRAY[0] *  (NS_SCALE_FACTOR_NUMERATOR/NS_SCALE_FACTOR_DENOMINATOR) * 10**(-NS_UNIT_POWER)
            
            GROUND_MOTION_ARRAY[1] = GROUND_MOTION_ARRAY[1] - EW_OFFSET
            GROUND_MOTION_ARRAY[1] = GROUND_MOTION_ARRAY[1] *  (EW_SCALE_FACTOR_NUMERATOR/EW_SCALE_FACTOR_DENOMINATOR)  * 10**(-EW_UNIT_POWER)
            
            GROUND_MOTION_ARRAY[2] = GROUND_MOTION_ARRAY[2] - UD_OFFSET
            GROUND_MOTION_ARRAY[2] = GROUND_MOTION_ARRAY[2] *  (UD_SCALE_FACTOR_NUMERATOR/UD_SCALE_FACTOR_DENOMINATOR) * 10**(-UD_UNIT_POWER)
        
        GROUND_MOTION_ARRAY = GROUND_MOTION_ARRAY[:,:-1]
        
        metadata = {}
        if DataBlockLength == 144:
            metadata["Earthquake"] = {}
            metadata["Earthquake"]["OT"] =(EQOT.isoformat(timespec='milliseconds'))
            metadata["Earthquake"]["EQScale"] = EQ_Scale
            metadata["Earthquake"]["Latitude"] = EQ_Latitude
            metadata["Earthquake"]["Longitude"] = EQ_Longitude
            metadata["Earthquake"]["Depth"] = EQ_Depth
        metadata["StationData"] = {}
        metadata["StationData"]["StationID"] = ObservationPointCode
        metadata["StationData"]["Latitude"] = StationLatitude
        metadata["StationData"]["Longitude"] = StationLongitude
        metadata["StationData"]["Elevation"] = StationElevation
        metadata["Recording"] = {}
        RecordingStartTime = (ParseTime(DataStartTime.decode('ASCII')) - timedelta(hours=9))
        metadata["Recording"]["StartTimeUTC"]  = RecordingStartTime.isoformat(timespec='milliseconds')
        metadata["Recording"]["EndTimeUTC"]  = (RecordingStartTime + timedelta(seconds=MeasurementTimeLength[0]*0.1)).isoformat(timespec='milliseconds')
        metadata["Recording"]["SamplingRateHZ"]  = SamplingRate
        metadata["Recording"]["CalibrationNS"] = NS_SCALE_FACTOR_NUMERATOR/NS_SCALE_FACTOR_DENOMINATOR * 10**(-NS_UNIT_POWER)
        metadata["Recording"]["OffsetNS"] = NS_OFFSET
        metadata["Recording"]["UnitNS"] = EW_UNIT_TYPE

        metadata["Recording"]["CalibrationEW"] = EW_SCALE_FACTOR_NUMERATOR/EW_SCALE_FACTOR_DENOMINATOR * 10**(-EW_UNIT_POWER)
        metadata["Recording"]["OffsetEW"] = EW_OFFSET
        metadata["Recording"]["UnitEW"] = EW_UNIT_TYPE

        metadata["Recording"]["CalibrationUD"] = UD_SCALE_FACTOR_NUMERATOR/UD_SCALE_FACTOR_DENOMINATOR * 10**(-UD_UNIT_POWER)
        metadata["Recording"]["OffsetUD"] = UD_OFFSET
        metadata["Recording"]["UnitUD"] = UD_UNIT_TYPE

        
        
        return GROUND_MOTION_ARRAY, metadata