import pandas as pd
import numpy as np
import os


class DataProcess:
    def __init__(self, table1=None, table2=None):
        self.df1 = pd.read_csv(table1) if table1 != None else table1

    
    def processA(self, start_t=None, end_t=None, df=None):
        df1 = self.df1 if df == None else df

        if start_t == None or end_t == None:
            df_a = df1
        else:
            df_a = df1[(df1['Molding Time'] >= start_t) & (df1['Molding Time'] <= end_t)]
        df_a = df_a.melt(id_vars=['Molding Time', 'Elapsed Time'])

        return df_a

    
    def processB(self, start_t=None, end_t=None, ranges=[1.5, 3, 4.5], df=None):
        df1 = self.df1 if df == None else df
        sensors = df1.columns[-4:]

        if start_t == None or end_t == None:
            df_b = df1[-30*301:]
        else:
            df_b = df1[(df1['Molding Time'] >= int(start_t)) & (df1['Molding Time'] <= int(end_t))]
        # print(df_b.shape)
        
        df_b = df_b.groupby('Molding Time').max()
        df_b.drop('Elapsed Time', axis=1, inplace=True)
        mean = df_b.mean()
        std = df_b.std()
        
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
        cl_df.to_csv('max_cl.csv')

        return cl_df

    
    def processC(self, start_t, end_t, sensor='1:9738-1-T'):
        df2 = pd.read_csv('max_cl.csv', index_col=0)
        self.max_cl = df2[sensor]

        file_c = sensor.split(':')[0] + '_max_log.csv'

        if os.path.isfile(file_c):
            df_c = pd.read_csv(file_c)
            log_date = self.date_process(start_t)
            df_c = df_c[df_c['Date'] == log_date]
            df_c['index'] = df_c['index'].apply(lambda i: str(i).zfill(5))
        else:
            df_c = self.df1.loc[:, ['Molding Time', sensor]]
            df_c = df_c[(df_c['Molding Time'] >= start_t) & (df_c['Molding Time'] <= end_t)]

            df_c = df_c.groupby('Molding Time').max()
            df_c.reset_index(inplace=True)

            df_c['index'] = df_c.index.to_series().apply(lambda i: str(i).zfill(5))
            df_c['Date'] = df_c['Molding Time'].apply(self.date_process)
            df_c['time'] = df_c['Molding Time'].apply(self.time_process)
            df_c = df_c.drop('Molding Time', axis=1)
            df_c = df_c[['index', 'Date', 'time', sensor]]
            df_c.columns = ['index', 'Date', 'time', 'max']

            df_c['region'] = df_c['max'].apply(self.cl_region)
            df_c['label'] = [None for i in range(len(df_c))]
            df_c['record'] = [None for i in range(len(df_c))]
            
            df_c.to_csv(file_c, index=False)

        # self.df3 = df_c
        return df_c

    
    def date_process(self, t):
        t = str(t)
        return '20%s-%s-%s' % (t[:2], t[2:4], t[4:6])

    
    def time_process(self, t):
        t = str(t)
        return '%s:%s:%s' % (t[6:8], t[8:10], t[10:12])

    
    def cl_region(self, x):
        max_cl = self.max_cl

        if x <= max_cl['ucl_1.5'] and x >= max_cl['lcl_1.5']:
            return '< 1.5'
        elif x <= max_cl['ucl_3'] and x >= max_cl['lcl_3']:
            return '1.5 ~ 3'
        elif x <= max_cl['ucl_4.5'] and x >= max_cl['lcl_4.5']:
            return '3 ~ 4.5'
        else:
            return '> 4.5'
