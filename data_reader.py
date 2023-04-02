import pandas as pd
import os
from functools import lru_cache
import datetime as dt

TS_ERP = 'ERP'


def load_all_data_sets():

    data_sets = {}

    df_erp = pd.read_excel('dataset.xlsx', sheet_name='SHILLER', skiprows=3).iloc[:, 1:4]
    df_erp['date'] = df_erp['BOM'].apply(lambda x:  dt.datetime.strptime("{:.2f}.01".format(x), "%Y.%m.%d"))
    data_sets[TS_ERP] = df_erp



    return data_sets


def main():

    load_all_data_sets()


if __name__ == '__main__':
    main()
