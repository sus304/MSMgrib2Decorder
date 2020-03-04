# MSMgrib2Decorder
気象庁が提供するMSM数値予報GPVのgribファイルをデコードして地上から上層までの風でpandas.DataFrameを生成するスクリプト。

gribファイルの処理ではNOAAが提供するデコードツールであるwgrib2が標準的であるが、
データをpandasで処理するには一旦ファイル出力を噛ませる必要があるので、風に絞ることでpythonネイティブでデコードできるツールを作成。

## Usage
``` Python
from MSMgribDecorder import decord_MSMwind

df_result = decord_MSMwind("Z__...Lsurf...bin", "Z__...L-pall...bin", 25.0, 130.0, 3):
```

## input
1st argument: 地表面grib2ファイル(Z__C_RJTD_yyyymmddhh0000_MSM_GPV_Rjp_Lsurf_FH00-15_grib2.bin)

2nd argument: 気圧面grib2ファイル(Z__C_RJTD_yyyymmddhh0000_MSM_GPV_Rjp_L-pall_FH00-15_grib2.bin)

3rd argument: 緯度[deg]

4th argument: 経度[deg]

5th argument: gribファイル計算時刻から取得する予報時刻の差分時間(0, 3, 6, 9, ...のようにgribファイルの上限に応じて3時間毎)

## output
pandas.DataFrame

|  height(高度[m])  |  pressure(気圧[kPa])  |  u-wind(東西方向の風速[m/s])  |  v-wind(南北方向の風速[m/s])  |  wind_velocity(風速[m/s])  |  wind_direction(北から時計回りの風向[deg])  |
| ---- | ---- | ---- | ---- | ---- | ---- |
|  10  |  101.9  |  -2.0  |  2.0  |  2.83  |  315.0  |
|  130.0  |  100.0  |  .  |  .  |  .  |  .  |
|  .  |  .  |  .  |  .  |  .  |  .  |
|  .  |  .  |  .  |  .  |  .  |  .  |


## License
MIT License