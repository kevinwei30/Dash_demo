import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.svm import OneClassSVM
import pickle
from .db_connectors import RawDBConnector, PreprocessedDBConnector, RecordDBConnector
from .model_operations import SPCModel, AnomalyModel



def one_mold_features(df, window_size):
    """單模數據特徵擷取
    
    Parameters
    ----------
    df : pandas.DataFrame
        單模數據
    window_size : int
        滑動窗格大小
    """
    n_sensors = df.shape[1] - 2
    # molding_time = df['Molding Time'].tolist()[0]

    data = df.iloc[:, 2:]
    cols = data.columns

    interval = window_size // 2

    s_mean = data.rolling(window_size).mean()[::interval][2:]
    s_max = data.rolling(window_size).max()[::interval][2:]
    # s_min = data.rolling(window_size).min()[::interval][2:]
    # s_sum = data.rolling(window_size).sum()[::interval][2:]

    features = ['mean', 'max']
    # features = ['mean', 'max', 'min', 'sum']

    all_features = []
    for c in cols:
        f_mean = s_mean[c].tolist()
        f_max = s_max[c].tolist()
        # f_min = s_min[c].tolist()
        # f_sum = s_sum[c].tolist()
        
        all_features += f_mean + f_max
        # all_features.append(f_mean + f_max + f_min + f_sum)

    return all_features


def get_features(df, window_size=10, length=401):
    """特徵工程for異常檢測
    
    Parameters
    ----------
    df : pandas.DataFrame
        成型模內壓數據
        shape = (n * m, s+2)
        n為模數，m為每模sample數量，s為sensor數量

        格式範例如下:
        df_a.head()
                     Molding Time  Elapsed Time  sensor1  sensor2  sensor3  sensor4
        0     2019-10-29 20:54:34          0.00      0.0      0.0      0.0      0.0
        1     2019-10-29 20:54:34          0.02      0.0      0.0      0.0      0.0
        2     2019-10-29 20:54:34          0.04      0.0      0.1      0.0      0.0
        3     2019-10-29 20:54:34          0.06      0.2      0.2      0.0      0.0
        4     2019-10-29 20:54:34          0.08      0.5      0.2      0.2      0.0
        
    window_size : int
        滑動窗格大小，取統計特徵時使用，預設為10

    length : int
        每模取的數據量，預設為401，代表從0.00秒取到8.00秒(每筆間隔為0.02秒)
    """
    n_sensors = df.shape[1] - 2
    s_cols = df.columns[2:]
    mold_group = df.groupby('Molding Time')

    f_data = []
    # for group in tqdm(mold_group, ascii=True):
    for group in mold_group:
        tmp_df = group[1]
        tmp_length = tmp_df.shape[0]
        if tmp_length > length:
            tmp_df = tmp_df.iloc[:length, :]
        elif tmp_length < length:
            raise ValueError('Not enough data points in single molding cycle.')

        f_row = one_mold_features(tmp_df, window_size)
        f_data.append([group[0]] + f_row)

    f_data = np.array(f_data)
    f_n = f_data.shape[1] // n_sensors
    f_cols = ['Molding Time']
    for i in range(n_sensors):
        for j in range(f_n):
            f_cols.append('feature{}_{}'.format(i+1, j+1))

    f_df = pd.DataFrame(f_data, columns=f_cols)

    return f_df

    """
    f_df.head()

             Molding Time feature1_1 feature1_2 feature1_3  ... feature4_156 feature4_157 feature4_158
    0 2019-10-29 20:54:34       0.22       0.13       0.03  ...            0            0          0.1
    1 2019-10-29 20:54:46       0.53       0.37       0.08  ...            0            0            0
    2 2019-10-29 20:54:58       0.43        0.3       0.09  ...            0            0            0
    3 2019-10-29 20:55:11       0.33       0.36       0.23  ...          0.3          0.3          0.1
    4 2019-10-29 20:55:23       0.43       0.29       0.08  ...          0.4          0.4          0.3
    """


def sensor_table_to_feature_table(table, start_t, end_t, window_size=10):
    if 'sensor' not in table:
        raise ValueError('table : must be a sensor data table name.')

    rawDB = RawDBConnector()
    df = rawDB.get_data(table=table, start_time=start_t, end_time=end_t)

    feature_df = get_features(df, window_size)

    feature_table = table.replace('sensor', 'feature')
    preDB = PreprocessedDBConnector()
    preDB.add_data(table=feature_table, new_df=feature_df)


def feature_table_to_anomalylog_table(table, start_t, end_t):
    if 'feature' not in table:
        raise ValueError('table : must be a feature data table name.')

    preDB = PreprocessedDBConnector()
    f_df = preDB.get_data(table=table, start_time=start_t, end_time=end_t)

    machine_id = int(table.replace('feature', ''))
    ad_model = AnomalyModel()
    
    anomalylog_df = ad_model.call_model(machine_id, f_df)

    log_table = table.replace('feature', 'anomalylog')
    recordDB = RecordDBConnector()
    recordDB.add_data(table=log_table, new_df=anomalylog_df)


def get_max_values(df):
    tmp_df = df.drop('Elapsed Time', axis=1, inplace=False)
    max_df = tmp_df.groupby('Molding Time').max()
    max_df.reset_index(inplace=True)
    
    return max_df

    """
    max_df.head()

             Molding Time  sensor1  sensor2  sensor3  sensor4
    0 2019-10-29 20:54:34      0.5      0.5      0.4      0.2
    1 2019-10-29 20:54:46      0.7      0.5      0.7      0.3
    2 2019-10-29 20:54:58      0.9      0.6      0.3      0.1
    3 2019-10-29 20:55:11      0.6      0.4      0.4      0.4
    4 2019-10-29 20:55:23      0.8      0.7      0.3      0.7
    """


def sensor_table_to_max_table(table, start_t, end_t):
    if 'sensor' not in table:
        raise ValueError('table : must be a sensor data table name.')

    rawDB = RawDBConnector()
    df = rawDB.get_data(table=table, start_time=start_t, end_time=end_t)

    max_df = get_max_values(df)
    # print(max_df.shape)

    max_table = table.replace('sensor', 'max')
    preDB = PreprocessedDBConnector()
    preDB.add_data(table=max_table, new_df=max_df)


def cl_region(cl, x):
    if x <= cl['ucl_1.5'] and x >= cl['lcl_1.5']:
        return '< 1.5'
    elif x <= cl['ucl_3'] and x >= cl['lcl_3']:
        return '1.5 ~ 3'
    elif x <= cl['ucl_4.5'] and x >= cl['lcl_4.5']:
        return '3 ~ 4.5'
    else:
        return '> 4.5'


def generate_log(df, spc_df):
    log_df = df.copy()
    sensor_cols = df.columns[1:]

    for col in sensor_cols:
        data = df[col].values
        cl = spc_df[col]
        spc_log = [cl_region(cl, x) for x in data]
        log_df[col] = spc_log

    none_list = [None for i in range(log_df.shape[0])]
    log_df['label'] = none_list
    log_df['record'] = none_list

    return log_df

    """
    log_df.head()

             Molding Time sensor1  sensor2 sensor3 sensor4 label record
    0 2019-10-29 20:54:34   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
    1 2019-10-29 20:54:46   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
    2 2019-10-29 20:54:58   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
    3 2019-10-29 20:55:11   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
    4 2019-10-29 20:55:23   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None

    註: label、record使用None初始化，如有值需為str
    """


def max_table_to_spclog_table(table, start_t, end_t):
    if 'max' not in table:
        raise ValueError('table : must be a max data table name.')

    preDB = PreprocessedDBConnector()
    max_df = preDB.get_data(table=table, start_time=start_t, end_time=end_t)

    machine_id = int(table.replace('max', ''))
    spc = SPCModel()
    spc_df = spc.get_model(machine_id)
    spc_df.index = spc_df['cl_type']

    spclog_df = generate_log(max_df, spc_df)

    log_table = table.replace('max', 'spclog')
    recordDB = RecordDBConnector()
    recordDB.add_data(table=log_table, new_df=spclog_df)

