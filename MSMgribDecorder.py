##
# GRIB2 File Decorder
# Author: Susumu Tanaka
# License: MIT License
##

### Ref.
# 配信資料に関する技術情報 第500号 別紙2-2 -GRIB2通報式によるメソ数値予報モデル格子点値データフォーマット- /by気象庁予報部
# 国際気象通報式・別冊 /by気象庁

import struct
import datetime
import numpy as np
import pandas as pd


def _decord(grib2_file_path, lat, lon, delta_hours):
    # input
    lat_input = int(lat * 1e6)
    lon_input = int(lon * 1e6)

    # output
    h_list = []
    p_list = []
    u_list = []
    v_list = []

    f = open(grib2_file_path, 'rb')

    readed_byte = 0

    # 0th section - indicate section
    ########################################################
    section_size = 16
    buf = f.read(section_size)
    if buf[0:4] != b'GRIB':
        print('Error! Not found GRIB code.')
        exit()
    if buf[7] != 2:
        print('Un-supported GRIB version.')
        exit()
    file_size = int.from_bytes(buf[8:16], 'big')
    readed_byte += section_size

    # 1st section - identify section
    ########################################################
    section_size = int.from_bytes(f.read(4), 'big')
    buf = f.read(section_size - 4)
    if buf[0] != 1:
        print('Un-match 1st-section number.')
        exit()
    year = int.from_bytes(buf[8:10], 'big')
    month = buf[10]
    day = buf[11]
    hour = buf[12]
    minute = buf[13]
    second = buf[14]
    datetime_ref = datetime.datetime(year, month, day, hour, minute, second)

    readed_byte += section_size

    if buf[15] != 0:  # making status
        print('Error! Testing.')
        exit()

    # 2nd section - local area section
    ########################################################
    # Non-Use

    # 3rd section - define mesh section
    ########################################################
    section_size = int.from_bytes(f.read(4), 'big')
    buf = f.read(section_size - 4)
    if buf[0] != 3:
        print('Un-match 3rd-section number.')
        exit()
    
    mesh_size = int.from_bytes(buf[2:6], 'big')

    if buf[10] != 6:  # R6371kmの球モデル
        print('Error! Missing Earth model.')
        exit()
    
    mesh_size_lon = int.from_bytes(buf[26:30], 'big') - 1
    mesh_size_lat = int.from_bytes(buf[30:34], 'big')

    lat_init = int.from_bytes(buf[42:46], 'big')
    lon_init = int.from_bytes(buf[46:50], 'big')
    lat_end = int.from_bytes(buf[51:55], 'big')
    lon_end = int.from_bytes(buf[55:59], 'big')
    delta_lon = int.from_bytes(buf[59:63], 'big')
    delta_lat = int.from_bytes(buf[63:67], 'big')

    scanning_mode = buf[67]
    if scanning_mode != 0:
        print('Error! Un-match scanning mode.')
        exit()

    readed_byte += section_size

    flag_pickup = False
    while readed_byte <= file_size-4-1:
        # 4th section - define product section
        ########################################################
        section_size = int.from_bytes(f.read(4), 'big')
        buf = f.read(section_size - 4)
        if buf[0] != 4:
            print('Un-match 4th-section number.')
            exit()

        product_template_number = int.from_bytes(buf[3:5], 'big')
        param_category = buf[5]
        param_number = buf[6]

        if buf[8] != 31:  # Meso value forecast
            print('Error! Not MSM.')
            exit()

        forecast_deltatime = int.from_bytes(buf[14:18], 'big')
        forecast_datetime = datetime_ref + datetime.timedelta(hours=forecast_deltatime)

        if forecast_deltatime == delta_hours and product_template_number == 0:
            if param_category == 2 or param_category == 3:
                flag_pickup = True
        else:
            flag_pickup = False
        # flag_pickup = True

        if flag_pickup:
            level = buf[18]
            sign = buf[19] >> 7
            level_scale_factor = buf[19] & 0b01111111
            if sign:
                level_scale_factor = -level_scale_factor
            level_value = int.from_bytes(buf[20:24], 'big')

        readed_byte += section_size
        
        # 5th section - data presentation section
        ########################################################
        section_size = int.from_bytes(f.read(4), 'big')
        buf = f.read(section_size - 4)
        if buf[0] != 5:
            print('Un-match 5th-section number.')
            exit()
        if int.from_bytes(buf[5:7], 'big') != 0:
            print('Error! Un-match data presentation template')
            exit()
        
        if flag_pickup:
            ref_value = struct.unpack('>f', buf[7:11])[0]
            int_16bit = int.from_bytes(buf[11:13], 'big')
            bin_factor = int_16bit  & 0b0111111111111111
            if (int_16bit >> 15) == 1:
                bin_factor = -bin_factor
            int_16bit = int.from_bytes(buf[13:15], 'big')
            dec_factor = int_16bit  & 0b0111111111111111
            if (int_16bit >> 15) == 1:
                dec_factor = -dec_factor
            press_value_bit = buf[15]
            if press_value_bit != 12:
                print('Error! Miss-match data bit size.')
                exit()

        readed_byte += section_size

        # 6th section - bitmap section
        ########################################################
        section_size = int.from_bytes(f.read(4), 'big')
        buf = f.read(section_size - 4)
        if buf[0] != 6:
            print('Un-match 6th-section number.')
            exit()
        readed_byte += section_size

        # 7th section - data section
        ########################################################
        section_size = int.from_bytes(f.read(4), 'big')
        buf = f.read(section_size - 4)
        if buf[0] != 7:
            print('Un-match 7th-section number.')
            exit()

        if flag_pickup:
            index_count = 1
            i_lat = 0
            i_lon = 0
            for i in range(mesh_size):
                lat_itr = lat_init - delta_lat * i_lat
                lon_itr = lon_init + delta_lon * i_lon
                if lat_itr == lat_input and lon_itr == lon_input:
                    byte_16bit = buf[i+index_count:i+index_count+2]
                    if i % 2 == 0:
                        # 12 bit from head
                        int_16bit = int.from_bytes(byte_16bit, 'big')
                        int_12bit = int_16bit >> 4
                        value = (ref_value + int_12bit * 2 ** bin_factor) / 10 ** dec_factor
                    else:
                        # 12 bit from tail
                        int_16bit = int.from_bytes(byte_16bit, 'big')
                        int_12bit = int_16bit & 0b0000111111111111
                        value = (ref_value + int_12bit * 2 ** bin_factor) / 10 ** dec_factor
        
                    if param_category == 2:
                        if param_number == 2:
                            u_list.append(value)
                        elif param_number == 3:
                            v_list.append(value)
                    elif param_category == 3:
                        if param_number == 1:
                            p_list.append(value/1e3)
                        elif param_number == 5:
                            h_list.append(value)

                    break  # mesh loop
                if i % 2 == 1:
                    index_count += 1

                if i_lon > 0 and i_lon % mesh_size_lon == 0:
                    i_lon = 0
                    i_lat += 1
                else:
                    i_lon += 1

        readed_byte += section_size

    # 8th section - Terminate section
    ########################################################
    section_size = 4
    buf = f.read(section_size)
    if buf[0:4] != b'7777':
        print('Error! Not found terminate code.')
        exit()

    f.close()

    return h_list, p_list, u_list, v_list


def _sort(h, p, u, v):
    target = []
    for i in range(len(h)):
        target.append([h[i], p[i], u[i], v[i]])
    res = sorted(target)

    h_res = []
    p_res = []
    u_res = []
    v_res = []
    for i in range(len(h)):
        h_res.append(res[i][0])
        p_res.append(res[i][1])
        u_res.append(res[i][2])
        v_res.append(res[i][3])
    return h_res, p_res, u_res, v_res



def decord_MSMwind(surf_grib2_file_path, pall_grib2_file_path, lat, lon, delta_hours=0):
    height_list = []
    pressure_list = []
    u_wind_list = []
    v_wind_list = []

    h, p, u, v = _decord(surf_grib2_file_path, lat, lon, delta_hours)
    height_list.append(10.0)
    pressure_list.extend(p)
    u_wind_list.extend(u)
    v_wind_list.extend(v)

    h, p, u, v = _decord(pall_grib2_file_path, lat, lon, delta_hours)
    height_list.extend(h)
    pressure_list.extend([100.0, 97.5, 95.0, 92.5, 90.0, 85.0, 80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 25.0, 20.0, 15.0, 10.0])
    u_wind_list.extend(u)
    v_wind_list.extend(v)

    # altの順番チェック
    alt = 0
    for alt_itr in height_list:
        if alt_itr > alt:
            alt = alt_itr
        else:
            height_list, pressure_list, u_wind_list, v_wind_list = _sort(height_list, pressure_list, u_wind_list, v_wind_list)
        
    df_data = pd.DataFrame()
    df_data['height'] = height_list
    df_data['pressure'] = pressure_list
    df_data['u_wind'] = u_wind_list
    df_data['v_wind'] = v_wind_list

    wind_vel_list = np.sqrt(df_data['u_wind'] ** 2 + df_data['v_wind'] ** 2)
    wind_dir_list = np.rad2deg(np.arctan2(df_data['u_wind'], df_data['v_wind']) + np.pi)

    df_data['wind_velocity'] = wind_vel_list
    df_data['wind_direction'] = wind_dir_list

    return df_data



if __name__ == "__main__":
    pall_file = "Z__C_RJTD_yyyymmddhh0000_MSM_GPV_Rjp_L-pall_FH00-15_grib2.bin"
    surf_file = "Z__C_RJTD_yyyymmddhh0000_MSM_GPV_Rjp_Lsurf_FH00-15_grib2.bin"
    df = decord_MSMwind(surf_file, pall_file, 22.4, 130.0, 9)
    df.to_csv('debug.csv')
    
