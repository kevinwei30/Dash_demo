import pandas as pd
import numpy as np
# import requests
import os
import MySQLdb
import pickle
from abc import ABC, abstractmethod
from .db_connectors import PreprocessedDBConnector


class ModelOperations(ABC):

    """模型操作
    
    Attributes
    ----------
    request_url : str
        可以取得模型運型結果的API前綴位址
    """
    
    def __init__(self):
        self.request_url = ''

    @abstractmethod
    def call_model(self, machine_id, input_data):
        """呼叫模型API
        
        Parameters
        ----------
        input_data : numpy.ndarray
            要丟給模型的輸入數據
        """
        pass

    @abstractmethod
    def save_model(self, model):
        """儲存模型

        Notes
        -----
        模型Server目前只支援pickle檔案上傳，要將模型物件做轉換
        
        Parameters
        ----------
        model : estimator object
            要存到模型Server上的模型物件
        """
        pass

    @abstractmethod
    def train_model(self, train_data):
        """訓練模型
        
        Parameters
        ----------
        train_data : numpy.ndarray
            用於訓練模型的訓練數據
        """
        pass


class SPCModel(ModelOperations):

    """SPC模型
    
    Notes
    -----
    根據每一模的模內壓最大值做SPC管制

    """
    
    def __init__(self):
        host = '10.60.10.140'
        user = 'kevinwei'
        passwd = 'ibdo123'
        db_name = 'ids_molding'

        self.db = MySQLdb.connect(host, user, passwd, db_name)
        self.cursor = self.db.cursor()

    def call_model(self, machine_id, input_data):
        # model API...
        return

    def get_model(self, machine_id):
        table = 'spc{}'.format(machine_id)
        query = 'select * from {:s}'.format(table)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        col_query = 'show columns from {:s}'.format(table)
        self.cursor.execute(col_query)
        col_results = self.cursor.fetchall()

        spc_df = pd.DataFrame(results)
        spc_df.columns = [col[0] for col in col_results]

        return spc_df

        """
        spc_df

           cl_type  sensor1  sensor2  sensor3  sensor4
        0  lcl_1.5     6.63     1.83     8.13     3.88
        1    lcl_3     5.99     0.00     7.39     1.21
        2  lcl_4.5     5.35     0.00     6.65     0.00
        3  ucl_1.5     7.92     7.86     9.62     9.22
        4    ucl_3     8.56    10.88    10.37    11.89
        5  ucl_4.5     9.20    13.90    11.11    14.56
        """

    def save_model(self, table, cl_df):
        if 'spc' not in table:
            raise ValueError('Only work for spc table.')

        keys = 'cl_type'
        sensor_list = []
        for col in cl_df.columns:
            if col != 'cl_type':
                keys += ', ' + col
                sensor_list.append(col)

        pre_query = 'insert into {:s} ({:s}) values'.format(table, keys)

        self.cursor.execute('truncate {:s}'.format(table))
        self.db.commit()

        for index, row in cl_df.iterrows():
            v_query = '"{:s}"'.format(row['cl_type'])
            for sensor in sensor_list:
                v_query += ', {:.2f}'.format(row[sensor])
            query = '{:s} ({:s})'.format(pre_query, v_query)

            self.cursor.execute(query)
            self.db.commit()

    def train_model(self, max_df, ranges):
        sensors = max_df.columns[1:]
        mean = max_df.mean()
        std = max_df.std()
        
        max_cls = []
        indexes = []
        for r in ranges:
            ucl = mean + std * r
            lcl = np.maximum(mean - std * r, 0)
            max_cls.append(ucl.tolist())
            max_cls.append(lcl.tolist())
            indexes += ['ucl_' + str(r), 'lcl_' + str(r)]
        max_cls = np.array(max_cls)

        cl_df = pd.DataFrame(max_cls, index=indexes, columns=sensors)
        cl_df['cl_type'] = indexes
        
        return cl_df

    def update_model(self, machine_id, start_time, end_time, ranges=[1.5, 3, 4.5]):
        preDBconnector = PreprocessedDBConnector()
        max_df = preDBconnector.get_data(table='max{}'.format(machine_id), 
                                         start_time=start_time, end_time=end_time)

        if max_df.shape[0] < 30:
            raise Exception('Data number < 30, can not proceed.')

        cl_df = self.train_model(max_df, ranges)

        spc_table = 'spc{}'.format(machine_id)
        self.save_model(spc_table, cl_df)


class AnomalyModel(ModelOperations):

    """異常偵測模型

    Notes
    -----
    根據每一模的模內壓特徵做異常偵測，可進一步做異常聚類
    
    Attributes
    ----------
    request_url : str
        可以取得模型運型結果的API前綴位址
    """
    
    def __init__(self):
        self.folder = 'anomaly/'

    def call_model(self, machine_id, f_df):
        cols = f_df.columns.tolist()
        cols.remove('Molding Time')

        col_n = len(cols)
        sensors = np.unique([c.split('_')[0] for c in cols])
        sensor_n = len(sensors)
        f_n = col_n // sensor_n

        models = self.get_models(machine_id)

        result_df = f_df.loc[:, ['Molding Time']]
        for i in range(sensor_n):
            n = i + 1
            x = f_df.iloc[:, 1+i*f_n:1+(i+1)*f_n].dropna(axis='columns')
            model = models['model{}_{}'.format(machine_id, n)]
            score = model.decision_function(x)
            result_df['sensor{}'.format(n)] = -score

        result_df = result_df.round(3)
        result_df['class'] = [None for i in range(f_df.shape[0])]

        return result_df

    def get_models(self, machine_id):
        pre = 'model{}'.format(machine_id)
        models = {}

        # folder = 'anomaly/'
        folder = self.folder
        files = os.listdir(folder)
        for file in files:
            if pre in file and '.pkl' in file:
                f = open(folder + file, 'rb')
                model = pickle.load(f)
                models[file.replace('.pkl', '')] = model

        return models

    def save_model(self, machine_id, models):
        folder = self.folder
        if not os.path.isdir(folder):
            os.mkdir(folder)

        for i, model in enumerate(models):
            with open(folder + 'model{}_{}.pkl'.format(machine_id, i+1), 'wb') as f:
                pickle.dump(model, f)

    def train_model(self, f_df):
        cols = f_df.columns.tolist()
        cols.remove('Molding Time')

        col_n = len(cols)
        sensors = np.unique([c.split('_')[0] for c in cols])
        sensor_n = len(sensors)
        f_n = col_n // sensor_n

        from sklearn.svm import OneClassSVM

        models = []
        for i in range(sensor_n):
            x = f_df.iloc[:, 1+i*f_n:1+(i+1)*f_n].dropna(axis='columns')
            model = OneClassSVM(gamma='auto', nu=0.05).fit(x)
            models.append(model)

        return models

    def update_model(self, machine_id, start_time, end_time):
        preDBconnector = PreprocessedDBConnector()
        f_df = preDBconnector.get_data(table='feature{}'.format(machine_id), 
                                       start_time=start_time, end_time=end_time)

        if f_df.shape[0] < 30:
            raise Exception('Data number < 30, can not proceed.')

        ad_models = self.train_model(f_df)
        self.save_model(machine_id, ad_models)


class TrendModel(ModelOperations):

    """趨勢預測模型

    Notes
    -----
    根據近期的模內壓數據變化，預測之後的趨勢走向
    
    Attributes
    ----------
    request_url : str
        可以取得模型運型結果的API前綴位址
    """
    
    def __init__(self):
        self.request_url = ''

    def call_model(self, input_data):
        # get_request = ''
        # response = requests.get(get_request)
        # result = response
        result = ''
        return result

    def save_model(self, model):
        # post_request = ''
        # response = requests.post(post_request, model=model)
        # result = response
        return 'model saved.'

    def train_model(self, train_data):
        # train model ...
        model = ''
        return model
