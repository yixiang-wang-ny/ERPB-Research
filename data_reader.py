import pandas as pd
import os
from functools import lru_cache
import datetime as dt
import dateutil.parser

TS_ERP = 'ERP'
TS_RECESSION = 'Recession'
TS_BREAK_EVEN = 'Breakeven Inflation'
TS_FED_FUND = 'Fed Fund Rate'
TS_NOMINAL = 'Nominal Rate'
TS_REAL_GDP = 'Real GDP'
TS_CREDIT_SPREAD = 'Credit Spread'
TS_MONETARY = 'Monetary'
TS_UNEMPLOYMENT = 'Unemployment'
TS_ACM_TERM_PREMIA = 'ACM Term Premia'


def _dt2date(x):

    return dt.date(x.year, x.month, x.day)


def load_all_data_sets():

    data_sets = {}

    df_erp = pd.read_excel('dataset.xlsx', sheet_name='SHILLER', skiprows=3).iloc[:, 1:4]
    # TODO: SWITCH TO MONTH END
    df_erp['Date'] = df_erp['BOM'].apply(lambda x:  dateutil.parser.parse("{:.2f}.01".format(x))).apply(_dt2date)
    df_erp = df_erp[['Date', 'CPI', 'Excess CAPE Yield']].set_index('Date')
    data_sets[TS_ERP] = df_erp

    df_recession = pd.read_excel('dataset.xlsx', sheet_name='Recession Periods')
    df_recession.columns = [x.strip() for x in df_recession.columns]
    df_recession['Peak'] = df_recession['Peak'].apply(dateutil.parser.parse).apply(_dt2date)
    df_recession['Trough'] = df_recession['Trough'].apply(dateutil.parser.parse).apply(_dt2date)
    data_sets[TS_RECESSION] = df_recession

    df_be = pd.read_excel('dataset.xlsx', sheet_name='Breakeven Inflation', skiprows=4).iloc[:, 2:]
    be_dfs = []
    for i in range(5):
        df_iter = df_be.iloc[:, 2*i: (2*i+2)]
        df_iter.columns = ['Date'] + [df_iter.columns[1]]
        df_iter = df_iter[df_iter['Date'].notnull()]
        df_iter.loc[:, 'Date'] = df_iter.loc[:, 'Date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
        be_dfs.append(df_iter.set_index('Date'))

    data_sets[TS_BREAK_EVEN] = pd.concat(be_dfs, axis=1).reset_index().rename(columns={'index': 'Date'}
                                                                              ).set_index('Date').sort_index()

    df_fed = pd.read_excel('dataset.xlsx', sheet_name='Nominal Rate', skiprows=6).iloc[:, 1:3]
    df_fed = df_fed[['observation_date', 'Fed Fund Effective Rate']]
    df_fed['Date'] = df_fed['observation_date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
    data_sets[TS_FED_FUND] = df_fed[df_fed['Date'].notnull()][['Date', 'Fed Fund Effective Rate']].set_index('Date')

    df_nominal = pd.read_excel('dataset.xlsx', sheet_name='Nominal Rate', skiprows=6).iloc[:, 1:]
    nominal_dfs = []
    for i in range(4):
        df_iter = df_nominal.iloc[:, (3 + 2*i): (3 + 2*i + 2)]
        df_iter.columns = ['Date'] + [df_iter.columns[1]]
        df_iter = df_iter[df_iter['Date'].notnull()]
        df_iter.loc[:, 'Date'] = df_iter.loc[:, 'Date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
        nominal_dfs.append(df_iter.set_index('Date'))
    data_sets[TS_NOMINAL] = pd.concat(nominal_dfs, axis=1).reset_index().rename(columns={'index': 'Date'}
                                                                                ).set_index('Date').sort_index()

    df_real_gdp = pd.read_excel('dataset.xlsx', sheet_name='Real GDP', skiprows=5).iloc[:, 2:]
    df_real_gdp['Date'] = df_real_gdp['observation_date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
    data_sets[TS_REAL_GDP] = df_real_gdp[['Date', 'RealGDP']].set_index('Date')

    df_credit_spread = pd.read_excel('dataset.xlsx', sheet_name='CreditSpread', skiprows=4).iloc[:, 1:]
    df_credit_spread['Date'] = df_credit_spread['Date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
    data_sets[TS_CREDIT_SPREAD] = df_credit_spread[['Date', 'US IG Spread', 'US HY Spread']].set_index('Date')

    df_money = pd.read_excel('dataset.xlsx', sheet_name='Real_M1_M2', skiprows=6).iloc[:, 2:]
    df_m1 = df_money[['Month End.1', 'Real_M1']].rename(columns={'Month End.1': 'Date'})
    df_m1['Date'] = df_m1['Date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
    df_m2 = df_money[['Month End', 'Real_M2']].rename(columns={'Month End': 'Date'})
    df_m2['Date'] = df_m2['Date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
    data_sets[TS_MONETARY] = pd.concat([df_m1.set_index('Date'), df_m2.set_index('Date')], axis=1)

    df_unemployment = pd.read_excel('dataset.xlsx', sheet_name='Unemployment Rate', skiprows=3).iloc[:, 3:].rename(
        columns={'Month End': 'Date'})
    df_unemployment['Date'] = df_unemployment['Date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
    data_sets[TS_UNEMPLOYMENT] = df_unemployment.set_index('Date')

    df_acm_term_premia = pd.read_excel('dataset.xlsx', sheet_name='ACM Term Premia').rename(
        columns={'DATE': 'Date'})
    df_acm_term_premia['Date'] = df_acm_term_premia['Date'].apply(lambda x: dateutil.parser.parse(str(x))).apply(_dt2date)
    data_sets[TS_ACM_TERM_PREMIA] = df_acm_term_premia.set_index('Date')

    return data_sets


def _date_month_format(x):
    return x.strftime('%b-%Y')


def consolidate_time_series():

    data_sets = load_all_data_sets()

    for k in data_sets:
        if k == 'Recession':
            continue

        df = data_sets[k].sort_index().reset_index()
        df['MonthYear'] = df['Date'].apply(_date_month_format)
        data_sets[k] = df

    dfs = []

    recession_periods = [
        (row[0], row[1]) for _, row in data_sets[TS_RECESSION].iterrows()
    ]

    def _get_recession(x):
        for recession_start, recession_end in recession_periods:
            if recession_start <= x <= recession_end:
                return f'{recession_start.strftime("%Y/%m")}-{recession_end.strftime("%Y/%m")}'

        return None

    df_erp = data_sets[TS_ERP]
    df_erp['Recession Period'] = df_erp['Date'].apply(_get_recession)
    df_erp['In Recession'] = df_erp['Recession Period'].notnull()
    df_erp['CPI Change'] = df_erp['CPI'] - df_erp['CPI'].shift(1)

    dfs.append(df_erp.set_index('MonthYear')[['Date', 'Excess CAPE Yield', 'CPI', 'CPI Change', 'Recession Period', 'In Recession']])

    df_be = data_sets[TS_BREAK_EVEN]
    df_be_month_end = df_be.groupby('MonthYear').tail(1)
    dfs.append(df_be_month_end.set_index('MonthYear').drop('Date', axis=1))

    df_fed_fund = data_sets[TS_FED_FUND][['MonthYear', 'Fed Fund Effective Rate']]
    dfs.append(df_fed_fund.groupby('MonthYear').tail(1).set_index('MonthYear'))

    df_nominal = data_sets[TS_NOMINAL]
    df_nominal_month_end = df_nominal.groupby('MonthYear').tail(1)
    dfs.append(df_nominal_month_end.set_index('MonthYear').drop('Date', axis=1))

    df_real_gdp = data_sets[TS_REAL_GDP]
    dfs.append(df_real_gdp.set_index('MonthYear').drop('Date', axis=1))

    df_credit_spread = data_sets[TS_CREDIT_SPREAD]
    df_ts_monetary = data_sets[TS_MONETARY]
    df_unemployment = data_sets[TS_UNEMPLOYMENT]
    df_acm_term_premia = data_sets[TS_ACM_TERM_PREMIA]

    df_all = pd.concat([
        df_erp.set_index('MonthYear').drop('Date', axis=1)[['Excess CAPE Yield', 'CPI']]
    ])


    return



def main():

    consolidate_time_series()


if __name__ == '__main__':
    main()
