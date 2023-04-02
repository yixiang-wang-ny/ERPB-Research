import pandas as pd
import os
from functools import lru_cache
import datetime as dt
import dateutil.parser

TS_ERP = 'ERP'


def _dt2date(x):

    return dt.date(x.year, x.month, x.day)


def load_all_data_sets():

    data_sets = {}

    df_erp = pd.read_excel('dataset.xlsx', sheet_name='SHILLER', skiprows=3).iloc[:, 1:4]
    df_erp['Date'] = df_erp['BOM'].apply(lambda x:  dateutil.parser.parse("{:.2f}.01".format(x))).apply(_dt2date)
    df_erp = df_erp[['Date', 'CPI', 'Excess CAPE Yield']].set_index('Date')
    data_sets[TS_ERP] = df_erp



    return data_sets


def main():

    load_all_data_sets()


if __name__ == '__main__':
    main()
