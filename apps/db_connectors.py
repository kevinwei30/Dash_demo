import pandas as pd
import numpy as np
import os
import MySQLdb
from datetime import datetime as dt
# from tqdm import tqdm
from abc import ABC, abstractmethod


class DBConnector(ABC):

    """DB連接器
    
    Notes
    -----
    連接場域的數據資料庫，要根據DB種類來撰寫相應的程式

    """

    @abstractmethod
    def get_data(self, table, start_time, end_time):
        """取得數據
        
        Parameters
        ----------
        table : str
            表的名稱
        start_time : int
            起始時間，ex.190821080000，代表2019/08/21的08:00:00
        end_time : int
            中止時間，ex.190821235959，代表2019/08/21的23:59:59
        """
        pass

    def update_data(self, table, time, values):
        """更新一筆數據
        
        Parameters
        ----------
        table : str
            表的名稱
        time : int
            要更新的那筆數據的時間戳
        values : dict
            要更新的數據
        """
        pass

    def add_data(self, table, values):
        """新增數據
        
        Parameters
        ----------
        table : str
            表的名稱
        values : list of dict
            要新增的數據
        """
        pass

    def delete_data(self, table, start_time, end_time):
        """刪除數據
        
        Parameters
        ----------
        table : str
            表的名稱
        start_time : int
            起始時間
        end_time : int
            中止時間
        """
        pass


class RawDBConnector(DBConnector):

    """原始數據DB連接器

    Notes
    -----
    連接場域的原始數據資料庫，所以只能取得資料，不做其他操作
    
    """
    
    def __init__(self):
        host = '10.60.10.140'
        user = 'kevinwei'
        passwd = 'ibdo123'
        db_name = 'ids_molding'

        self.db = MySQLdb.connect(host, user, passwd, db_name)
        self.cursor = self.db.cursor()

    def get_data(self, table, start_time, end_time):
        start_t = dt.strftime(start_time, '%Y-%m-%d %H:%M:%S')
        end_t = dt.strftime(end_time, '%Y-%m-%d %H:%M:%S')

        query = 'select * from {:s} where date_time >= "{:s}" and date_time <= "{:s}"'\
                .format(table, start_t, end_t)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        col_query = 'show columns from {:s}'.format(table)
        self.cursor.execute(col_query)
        col_results = self.cursor.fetchall()

        cols = ['Molding Time', 'Elapsed Time']
        cols += [col[0] for col in col_results[2:]]

        if len(results) > 0:
            sensor_df = pd.DataFrame(results, columns=cols)
        else:
            sensor_df = pd.DataFrame(columns=cols)

        return sensor_df


class PreprocessedDBConnector(DBConnector):

    """前處理後數據DB連接器

    Notes
    -----
    原始數據經過前處理之後，存入"前處理後數據DB"。
    此DB要定期刪除過舊的數據。
    
    Attributes
    ----------
    passwd : str
        Description
    user : str
        Description
    """
    
    def __init__(self):
        host = '10.60.10.140'
        user = 'kevinwei'
        passwd = 'ibdo123'
        db_name = 'ids_molding'

        self.db = MySQLdb.connect(host, user, passwd, db_name)
        self.cursor = self.db.cursor()

    def get_data(self, table, start_time, end_time):
        if 'max' in table:
            data_df = self._get_max_data(table, start_time, end_time)
        elif 'sensor' in table:
            data_df = self._get_sensor_data(table, start_time, end_time)
        elif 'feature' in table:
            data_df = self._get_feature_data(table, start_time, end_time)
        else:
            raise ValueError('table name is not valid.')

        return data_df

    def _get_max_data(self, table, start_time, end_time):
        start_t = dt.strftime(start_time, '%Y-%m-%d %H:%M:%S')
        end_t = dt.strftime(end_time, '%Y-%m-%d %H:%M:%S')

        query = 'select * from {:s} where date_time >= "{:s}" and date_time <= "{:s}"'\
                .format(table, start_t, end_t)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        col_query = 'show columns from {:s}'.format(table)
        self.cursor.execute(col_query)
        col_results = self.cursor.fetchall()

        cols = ['Molding Time']
        cols += [col[0] for col in col_results[1:]]

        if len(results) > 0:
            max_df = pd.DataFrame(results, columns=cols)
        else:
            max_df = pd.DataFrame(columns=cols)

        return max_df

        '''
        max_df.head()

                 Molding Time  sensor1  sensor2  sensor3  sensor4
        0 2019-11-01 09:02:06      2.0      0.4      2.3      0.6
        1 2019-11-01 09:02:19      4.5      0.4      5.5      0.7
        2 2019-11-01 09:02:32      5.1      0.2      5.8      0.1
        3 2019-11-01 09:02:46      5.5      0.6      7.7      0.4
        4 2019-11-01 09:02:59      5.3      0.3      7.1      0.3
        '''

    def _get_sensor_data(self, table, start_time, end_time):
        start_t = dt.strftime(start_time, '%Y-%m-%d %H:%M:%S')
        end_t = dt.strftime(end_time, '%Y-%m-%d %H:%M:%S')

        query = 'select * from {:s} where date_time >= "{:s}" and date_time <= "{:s}"'\
                .format(table, start_t, end_t)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        col_query = 'show columns from {:s}'.format(table)
        self.cursor.execute(col_query)
        col_results = self.cursor.fetchall()

        cols = ['Molding Time', 'Elapsed Time']
        cols += [col[0] for col in col_results[2:]]

        if len(results) > 0:
            sensor_df = pd.DataFrame(results, columns=cols)
        else:
            sensor_df = pd.DataFrame(columns=cols)

        return sensor_df

        '''
        sensor_df.head()

           Molding Time  Elapsed Time  1:9738-1-T  2:9738-1-W  3:9738-2-T  4:9738-2-W
        0  190821125705          0.00         0.0         0.0         0.0         0.0
        1  190821125705          0.02         0.0         0.1         0.0         0.1
        2  190821125705          0.04         0.0         0.1         0.0         0.0
        3  190821125705          0.06         0.1         0.0         0.1         0.1
        4  190821125705          0.08         0.0         0.0         0.2         0.1
        '''

    def _get_feature_data(self, table, start_time, end_time):
        start_t = dt.strftime(start_time, '%Y-%m-%d %H:%M:%S')
        end_t = dt.strftime(end_time, '%Y-%m-%d %H:%M:%S')

        query = 'select * from {:s} where date_time >= "{:s}" and date_time <= "{:s}"'\
                .format(table, start_t, end_t)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        col_query = 'show columns from {:s}'.format(table)
        self.cursor.execute(col_query)
        col_results = self.cursor.fetchall()

        cols = ['Molding Time']
        cols += [col[0] for col in col_results[1:]]

        if len(results) > 0:
            f_df = pd.DataFrame(results, columns=cols)
        else:
            f_df = pd.DataFrame(columns=cols)

        return f_df

    def update_data(self, table, time, values):
        query = ''
        return 'data updated.'

    def add_data(self, table, new_df):
        if 'max' in table:
            self._add_max_data(table, new_df)
        elif 'feature' in table:
            self._add_feature_data(table, new_df)
        else:
            raise ValueError('table name is not valid.')

    def _add_max_data(self, table, max_df):
        """新增最大值數據到DB
        
        Parameters
        ----------
        table : str
            數據表名稱
        max_df : pandas.DataFrame
            用於更新的模內壓最大值df(格式如下)

            max_df.head()
                     Molding Time  sensor1  sensor2  sensor3  sensor4
            0 2019-10-29 20:54:34      0.5      0.5      0.4      0.2
            1 2019-10-29 20:54:46      0.7      0.5      0.7      0.3
            2 2019-10-29 20:54:58      0.9      0.6      0.3      0.1
            3 2019-10-29 20:55:11      0.6      0.4      0.4      0.4
            4 2019-10-29 20:55:23      0.8      0.7      0.3      0.7

            註: Molding Time的值為TimeStamp型別
        """
        keys = '(date_time'
        for i in range(max_df.shape[1]-1):
            keys += ', sensor{:d}'.format(i+1)
        keys += ')'

        pre_query = 'insert into {:s} {:s} values '.format(table, keys)

        # for row in tqdm(max_df.values, ascii=True):
        for row in max_df.values:
            t = row[0].to_pydatetime()
            t_str = t.strftime('%Y-%m-%d %H:%M:%S')
            v_query = '("{:s}"'.format(t_str)
            for v in row[1:]:
                v_query += ', {:.1f}'.format(v)
            v_query += ')'
            query = pre_query + v_query
            
            self.cursor.execute(query)
            self.db.commit()

    def _add_feature_data(self, table, f_df):
        f_cols = f_df.columns.tolist()

        keys = '(date_time'
        for col in f_cols[1:]:
            keys += ', {:s}'.format(col)
        keys += ')'

        pre_query = 'insert into {:s} {:s} values '.format(table, keys)

        # for row in tqdm(f_df.values, ascii=True):
        for row in f_df.values:
            t = row[0].to_pydatetime()
            t_str = t.strftime('%Y-%m-%d %H:%M:%S')
            v_query = '("{:s}"'.format(t_str)
            for v in row[1:]:
                v_query += ', {:.3f}'.format(v)
            v_query += ')'
            query = pre_query + v_query
            
            self.cursor.execute(query)
            self.db.commit()

    def delete_data(self, table, start_time, end_time):
        query = ''
        return 'data deleted.'


class RecordDBConnector(DBConnector):

    """紀錄數據DB連接器

    Notes
    -----
    前處理後數據會再經過模型運算，將結果存到"紀錄數據DB"。
    此DB數據會用來呈現在網頁頁面上，也要定期刪除過舊的數據。
    
    """
    
    def __init__(self):
        host = '10.60.10.140'
        user = 'kevinwei'
        passwd = 'ibdo123'
        db_name = 'ids_molding'

        self.db = MySQLdb.connect(host, user, passwd, db_name, use_unicode=True, charset='utf8')
        self.cursor = self.db.cursor()

    def get_data(self, table, start_time, end_time):
        if 'spclog' in table:
            data_df = self._get_spc_log(table, start_time, end_time)
        elif 'anomalylog' in table:
            data_df = self._get_anomaly_log(table, start_time, end_time)
        else:
            raise ValueError('table name is not valid.')

        return data_df

    def _get_spc_log(self, table, start_time, end_time):
        start_t = dt.strftime(start_time, '%Y-%m-%d %H:%M:%S')
        end_t = dt.strftime(end_time, '%Y-%m-%d %H:%M:%S')

        query = 'select * from {:s} where date_time >= "{:s}" and date_time <= "{:s}"'\
                .format(table, start_t, end_t)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        col_query = 'show columns from {:s}'.format(table)
        self.cursor.execute(col_query)
        col_results = self.cursor.fetchall()

        cols = ['Molding Time']
        cols += [col[0] for col in col_results[1:]]

        if len(results) > 0:
            log_df = pd.DataFrame(results, columns=cols)
        else:
            log_df = pd.DataFrame(columns=cols)

        return log_df

        '''
        log_df.head()

                 Molding Time sensor1  sensor2 sensor3  sensor4 label record
        0 2019-11-02 23:00:00   < 1.5  1.5 ~ 3   < 1.5  1.5 ~ 3  None   None
        1 2019-11-02 23:00:14   < 1.5    < 1.5   < 1.5  1.5 ~ 3  None   None
        2 2019-11-02 23:00:29   < 1.5    < 1.5   < 1.5  1.5 ~ 3  None   None
        3 2019-11-02 23:00:43   < 1.5    < 1.5   < 1.5    < 1.5  None   None
        4 2019-11-02 23:00:58   < 1.5    < 1.5   < 1.5    < 1.5  None   None
        '''

    def _get_anomaly_log(self, table, start_time, end_time):
        start_t = dt.strftime(start_time, '%Y-%m-%d %H:%M:%S')
        end_t = dt.strftime(end_time, '%Y-%m-%d %H:%M:%S')

        query = 'select * from {:s} where date_time >= "{:s}" and date_time <= "{:s}"'\
                .format(table, start_t, end_t)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        col_query = 'show columns from {:s}'.format(table)
        self.cursor.execute(col_query)
        col_results = self.cursor.fetchall()

        cols = ['Molding Time']
        cols += [col[0] for col in col_results[1:]]

        if len(results) > 0:
            log_df = pd.DataFrame(results, columns=cols)
        else:
            log_df = pd.DataFrame(columns=cols)

        return log_df

        '''
        log_df.head()
        
                 Molding Time  sensor1  sensor2  sensor3  sensor4 class
        0 2019-11-02 00:00:01    3.619    2.997    3.438    5.470  None
        1 2019-11-02 00:00:16    2.050    2.766    2.973    5.285  None
        2 2019-11-02 00:00:30    2.687    2.616    3.177    5.662  None
        3 2019-11-02 00:00:45    1.947    2.973    2.707    5.213  None
        4 2019-11-02 00:00:59    1.522    2.627    3.300    5.107  None
        '''

    def update_data(self, table, diff_df):
        if 'spclog' in table:
            self._update_spc_log(table, diff_df)
        elif 'anomalylog' in table:
            self._update_anomaly_log(table, diff_df)
        else:
            raise ValueError('table name is not valid.')

        return 'data updated.'

    def _null_check(self, inp):
        if isinstance(inp, str):
            if inp == '':
                return 'NULL'
            else:
                return '"{}"'.format(inp)
        elif inp == None:
            return 'NULL'
        elif np.isnan(inp):
            return 'NULL'
        else:
            return '"{}"'.format(inp)

    def _update_spc_log(self, table, diff_df):
        pre_query = 'update {:s} set '.format(table)
        sensor_n = diff_df.shape[1] - 3

        for row in diff_df.values:
            t = row[0].to_pydatetime()
            t_str = t.strftime('%Y-%m-%d %H:%M:%S')

            set_query = ''
            for i in range(sensor_n):
                set_query += 'sensor{}="{}", '.format(i+1, row[1+i])
            
            label = self._null_check(row[-2])
            record = self._null_check(row[-1])
            set_query += 'label={}, record={} where date_time="{:s}"'\
                         .format(label, record, t_str)
            query = pre_query + set_query

            self.cursor.execute(query)
            self.db.commit()

    def _update_anomaly_log(self, table, diff_df):
        pre_query = 'update {:s} set '.format(table)
        sensor_n = diff_df.shape[1] - 2

        for row in diff_df.values:
            t = row[0].to_pydatetime()
            t_str = t.strftime('%Y-%m-%d %H:%M:%S')

            set_query = ''
            for i in range(sensor_n):
                set_query += 'sensor{}={}, '.format(i+1, row[1+i])

            row_cls = self._null_check(row[-1])
            set_query += 'class={} where date_time="{:s}"'\
                         .format(row_cls, t_str)
            query = pre_query + set_query

            self.cursor.execute(query)
            self.db.commit()

    def add_data(self, table, new_df):
        if 'spclog' in table:
            self._add_spc_log(table, new_df)
        elif 'anomalylog' in table:
            self._add_anomaly_log(table, new_df)
        else:
            raise ValueError('table name is not valid.')

    def _add_spc_log(self, table, log_df):
        """新增SPC log紀錄到DB
        
        Parameters
        ----------
        table : str
            數據表名稱
        log_df : pandas.DataFrame
            用於更新的SPC log df(格式如下)

            log_df.head()
                     Molding Time sensor1  sensor2 sensor3 sensor4 label record
            0 2019-10-29 20:54:34   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
            1 2019-10-29 20:54:46   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
            2 2019-10-29 20:54:58   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
            3 2019-10-29 20:55:11   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None
            4 2019-10-29 20:55:23   > 4.5  3 ~ 4.5   > 4.5   > 4.5  None   None

            註: Molding Time的值為TimeStamp型別，sensor欄位皆為str型別
        """
        keys = '(date_time'
        for i in range(log_df.shape[1]-3):
            keys += ', sensor{:d}'.format(i+1)
        keys += ', label, record)'

        pre_query = 'insert into {:s} {:s} values '.format(table, keys)

        # for row in tqdm(log_df.values, ascii=True):
        for row in log_df.values:
            t = row[0].to_pydatetime()
            t_str = t.strftime('%Y-%m-%d %H:%M:%S')
            v_query = '("{:s}"'.format(t_str)
            for v in row[1:]:
                if v == None:
                    v_query += ', NULL'.format(v)
                else:
                    v_query += ', "{}"'.format(v)
            v_query += ')'
            query = pre_query + v_query
            
            self.cursor.execute(query)
            self.db.commit()

    def _add_anomaly_log(self, table, log_df):
        """新増異常檢測log紀錄到DB
        
        Parameters
        ----------
        table : str
            數據表名稱
        log_df : pandas.DataFrame
            用於更新的Anomaly log df(格式如下)

            log_df.head()
                     Molding Time  sensor1  sensor2  sensor3  sensor4 class
            0 2019-10-29 20:54:34   -0.026   -0.084   -0.065   -0.013  None
            1 2019-10-29 20:54:46   -0.261   -0.185   -0.180   -0.008  None
            2 2019-10-29 20:54:58   -0.228   -0.132   -0.054    0.022  None
            3 2019-10-29 20:55:11   -0.317   -0.096   -0.290   -0.106  None
            4 2019-10-29 20:55:23   -0.225   -0.186   -0.063   -0.258  None

            註: Molding Time的值為TimeStamp型別，sensor欄位皆為float型別
        """
        keys = '(date_time'
        for i in range(log_df.shape[1]-2):
            keys += ', sensor{:d}'.format(i+1)
        keys += ', class)'

        pre_query = 'insert into {:s} {:s} values '.format(table, keys)

        # for row in tqdm(log_df.values, ascii=True):
        for row in log_df.values:
            t = row[0].to_pydatetime()
            t_str = t.strftime('%Y-%m-%d %H:%M:%S')
            v_query = '("{:s}"'.format(t_str)
            for v in row[1:-1]:
                v_query += ', {}'.format(v)
            if row[-1] == None:
                v_query += ', NULL'.format(v)
            else:
                v_query += ', "{}"'.format(v)
            v_query += ')'
            query = pre_query + v_query
            
            self.cursor.execute(query)
            self.db.commit()

    def delete_data(self, table, start_time, end_time):
        query = ''
        return 'data deleted.'
