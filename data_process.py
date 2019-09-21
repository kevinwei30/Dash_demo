import pandas as pd
import numpy as np
import os
import pymongo


class DataProcess:
    def __init__(self):
        self.user = 'kevinwei'
        self.passwd = 'foxconnibdo'
        connect_str = 'mongodb+srv://{}:{}@cluster0-fazdx.mongodb.net/test?retryWrites=true&w=majority'.format(self.user, self.passwd)
        self.client = pymongo.MongoClient(connect_str)

        self.db = self.client.moldingData
        self.sensor9738 = self.db.sensor9738
        self.max9738 = self.db.max9738
        # self.cl9738 = self.db.cl9738
        # self.log9738 = self.db.log9738

        # self.df1 = pd.read_csv(table1) if table1 != None else table1


    def doc_to_df(self, doc):
        print('doc to df...')

        df = pd.DataFrame()
        for idx, d in enumerate(doc):
            # print(idx)
            new_df = pd.DataFrame(d['records'], columns=d['columns'])
            new_df['Molding Time'] = [d['Molding Time'] for i in range(len(new_df))]
            new_df['Elapsed Time'] = d['Elapsed Time']
            new_df = new_df[['Molding Time', 'Elapsed Time'] + d['columns']]
            df = pd.concat([df, new_df], ignore_index=True)

        return df


    def processA(self, start_t, end_t, mode='max'):
        query = {'Molding Time': {'$gt': start_t-1, '$lt': end_t+1}}

        # get sensor max values
        if mode == 'max':
            # doc = self.sensor9738.find(query, {'Molding Time': 1, 'columns': 1, 'max': 1})
            doc = self.max9738.find(query)

            data = []
            molding_time = []
            cols = []
            for idx, d in enumerate(doc):
                if idx == 0:
                    cols = d['columns']

                data.append(d['max'])
                molding_time.append(d['Molding Time'])

            df = pd.DataFrame(data, columns=cols)
            df['Molding Time'] = molding_time
            df_a = df[['Molding Time'] + cols]

            '''
            df_a.head()

               Molding Time  1:9738-1-T  2:9738-1-W  3:9738-2-T  4:9738-2-W
            0  190821000005        12.1        11.6        13.0        12.2
            1  190821000019        10.6        10.1        11.5        10.3
            2  190821000032        10.8        10.3        11.1        10.8
            3  190821000046        10.8        10.3        11.6        10.9
            4  190821000059        11.5        11.0        11.9        11.3
            '''
        
        else:
            doc = self.sensor9738.find(query)

            cols = []
            df = pd.DataFrame()
            for idx, d in enumerate(doc):
                if idx == 0:
                    cols = d['columns']

                new_df = pd.DataFrame(d['records'], columns=cols)
                new_df['Molding Time'] = [d['Molding Time'] for i in range(len(new_df))]
                new_df['Elapsed Time'] = d['Elapsed Time']
                new_df = new_df[['Molding Time', 'Elapsed Time'] + cols]
                df = pd.concat([df, new_df], ignore_index=True)

            df_a = df[['Molding Time', 'Elapsed Time'] + cols]

            '''
            df_a.head()

               Molding Time  Elapsed Time  1:9738-1-T  2:9738-1-W  3:9738-2-T  4:9738-2-W
            0  190821125705          0.00         0.0         0.0         0.0         0.0
            1  190821125705          0.02         0.0         0.1         0.0         0.1
            2  190821125705          0.04         0.0         0.1         0.0         0.0
            3  190821125705          0.06         0.1         0.0         0.1         0.1
            4  190821125705          0.08         0.0         0.0         0.2         0.1
            '''

        print(df_a.shape)

        return df_a

    
    def processB(self, start_t=None, end_t=None, ranges=[1.5, 3, 4.5]):

        if start_t == None or end_t == None:
            doc = self.sensor9738.find().sort('Molding Time', -1).limit(30)
            df_b = self.doc_to_df(doc)
        else:
            query = {'Molding Time': {'$gt': start_t-1, '$lt': end_t+1}}
            doc = self.sensor9738.find(query)
            df_b = self.doc_to_df(doc)

        print(df_b.shape)
        sensors = df_b.columns[-4:]
        
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
        cl_df.to_csv('datas/max_cl.csv')

        return cl_df

    
    def processC(self, start_t, end_t, sensor='1:9738-1-T'):
        if not os.path.isfile('datas/max_cl.csv'):
            self.processB()

        df2 = pd.read_csv('datas/max_cl.csv', index_col=0)
        self.max_cl = df2[sensor]

        file_c = 'datas/' + sensor.split(':')[0] + '_max_log.csv'

        if os.path.isfile(file_c):
            df_c = pd.read_csv(file_c)
            # df_c['index'] = df_c['index'].apply(lambda i: str(i).zfill(5))
            df_c['region'] = df_c['max'].apply(self.cl_region)
        else:
            df_c = self.df1.loc[:, ['Molding Time', sensor]]
            # df_c = df_c[(df_c['Molding Time'] >= start_t) & (df_c['Molding Time'] <= end_t)]

            df_c = df_c.groupby('Molding Time').max()
            df_c.reset_index(inplace=True)

            df_c['index'] = df_c.index.to_series()
            df_c['Date'] = df_c['Molding Time'].apply(self.date_process)
            df_c['time'] = df_c['Molding Time'].apply(self.time_process)
            df_c = df_c.drop('Molding Time', axis=1)
            df_c = df_c[['index', 'Date', 'time', sensor]]
            df_c.columns = ['index', 'Date', 'time', 'max']

            df_c['region'] = df_c['max'].apply(self.cl_region)
            df_c['label'] = [None for i in range(len(df_c))]
            df_c['record'] = [None for i in range(len(df_c))]
            
            df_c.to_csv(file_c, index=False)

        log_date = self.date_process(start_t)
        df_c = df_c[df_c['Date'] == log_date]
        df_c.reset_index(drop=True, inplace=True)
        df_c['index'] = df_c.index.to_series().apply(lambda i: str(i).zfill(5))
        
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
