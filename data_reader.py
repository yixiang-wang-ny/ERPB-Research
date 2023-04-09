import pandas as pd
import os
from functools import lru_cache
import datetime as dt
import dateutil.parser
import pandas.tseries.offsets as offsets
from functools import reduce
from sklearn import linear_model

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
    df_erp['Date'] = df_erp['Date'].apply(lambda x: _dt2date(x + offsets.MonthEnd()))
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

    recession_periods = [(
        row[0], row[1],
        _dt2date(dateutil.parser.parse(str(row[0] - 365 * offsets.Day()))),
        _dt2date(dateutil.parser.parse(str(row[1] + 365 * offsets.Day()))),
     ) for _, row in data_sets[TS_RECESSION].iterrows()]

    def _get_recession(x):
        for recession_start, recession_end, _, _ in recession_periods:
            if recession_start <= x <= recession_end:
                return f'{recession_start.strftime("%Y/%m")}-{recession_end.strftime("%Y/%m")}'

        return None

    def _get_recession_phase(x):
        for recession_start, recession_end, _, _ in recession_periods:
            if recession_start <= x <= recession_end:
                return f'In Recession'

        for recession_start, _, year_bf_recession_start, _ in recession_periods:
            if year_bf_recession_start <= x <= recession_start:
                return f'1Yr Before'

        for _, recession_end, _, year_after_recession_end in recession_periods:
            if recession_end <= x <= year_after_recession_end:
                return f'1Yr After'

        return 'Other time'

    df_erp = data_sets[TS_ERP]
    df_erp['Recession Phase'] = df_erp['Date'].apply(_get_recession_phase)
    df_erp['Recession Period'] = df_erp['Date'].apply(_get_recession)
    df_erp['In Recession'] = df_erp['Recession Period'].notnull()
    df_erp['CPI Change'] = df_erp['CPI'] - df_erp['CPI'].shift(1)
    df_erp['CPI Pct Change'] = (df_erp['CPI'] - df_erp['CPI'].shift(1)) / df_erp['CPI'].shift(1)

    dfs.append(df_erp.set_index('MonthYear')[[
        'Date', 'Excess CAPE Yield', 'CPI', 'CPI Change', 'Recession Phase', 'Recession Period', 'In Recession'
    ]])

    df_be = data_sets[TS_BREAK_EVEN]
    df_be_month_end = df_be.groupby('MonthYear').tail(1)
    dfs.append(df_be_month_end.set_index('MonthYear').drop('Date', axis=1))

    df_fed_fund = data_sets[TS_FED_FUND][['MonthYear', 'Fed Fund Effective Rate']]
    dfs.append(df_fed_fund.groupby('MonthYear').tail(1).set_index('MonthYear'))

    df_nominal = data_sets[TS_NOMINAL]
    df_nominal_month_end = df_nominal.groupby('MonthYear').tail(1)
    dfs.append(df_nominal_month_end.set_index('MonthYear').drop('Date', axis=1))

    df_real_irs = []
    for ts_nom, ts_be, name_real in [
        ('UST2Y', 'USGGBE02 Index', 'Real IR 2Y'), ('UST5Y', 'USGGBE05 Index', 'Real IR 5Y'),
        ('UST10Y', 'USGGBE10 Index', 'Real IR 10Y'), ('UST30Y', 'USGGBE30 Index', 'Real IR 30Y')
    ]:
        df_real_calc = pd.merge(
            df_nominal[['Date', ts_nom]], df_be[['Date', ts_be]], on=['Date'], how='outer'
        )
        df_real_calc[name_real] = df_real_calc[ts_nom] - df_real_calc[ts_be]
        df_real_calc['MonthYear'] = df_real_calc['Date'].apply(_date_month_format)

        df_real_irs.append(df_real_calc.sort_values('Date').groupby('MonthYear').tail(1)[['MonthYear', name_real]])

    df_real_all = reduce(lambda a, b: pd.merge(a, b, how='outer'), df_real_irs[1:], df_real_irs[0]).set_index(
        'MonthYear')
    dfs.append(df_real_all)

    df_real_gdp = data_sets[TS_REAL_GDP]
    df_real_gdp['RealGDP Annualized Growth 1yr'] = (df_real_gdp['RealGDP']/df_real_gdp['RealGDP'].shift(1*4)) - 1
    df_real_gdp['RealGDP Annualized Growth 3yr'] = ((df_real_gdp['RealGDP']/df_real_gdp['RealGDP'].shift(3*4)))**(1/3)-1
    df_real_gdp['RealGDP Annualized Growth 5yr'] = ((df_real_gdp['RealGDP'] / df_real_gdp['RealGDP'].shift(5*4))) ** (1/5)-1
    dfs.append(df_real_gdp.set_index('MonthYear').drop('Date', axis=1))

    df_credit_spread = data_sets[TS_CREDIT_SPREAD]
    df_credit_spread_month_end = df_credit_spread.groupby('MonthYear').tail(1)
    dfs.append(df_credit_spread_month_end.set_index('MonthYear').drop('Date', axis=1))

    df_ts_monetary = data_sets[TS_MONETARY]
    df_ts_monetary['Real_M1_Growth'] = df_ts_monetary['Real_M1'] - df_ts_monetary['Real_M1'].shift(1)
    df_ts_monetary['Real_M1_Pct_Growth'] = (df_ts_monetary['Real_M1'] - df_ts_monetary['Real_M1'].shift(1)) / df_ts_monetary['Real_M1'].shift(1)
    df_ts_monetary['Real_M2_Growth'] = df_ts_monetary['Real_M2'] - df_ts_monetary['Real_M2'].shift(1)
    df_ts_monetary['Real_M2_Pct_Growth'] = (df_ts_monetary['Real_M2'] - df_ts_monetary['Real_M2'].shift(1)) / df_ts_monetary['Real_M2'].shift(1)
    dfs.append(df_ts_monetary.set_index('MonthYear').drop('Date', axis=1))

    df_unemployment = data_sets[TS_UNEMPLOYMENT]
    dfs.append(df_unemployment.set_index('MonthYear').drop('Date', axis=1))

    df_acm_term_premia = data_sets[TS_ACM_TERM_PREMIA]
    df_acm_term_premia_month_end = df_acm_term_premia.groupby('MonthYear').tail(1)
    dfs.append(df_acm_term_premia_month_end.set_index('MonthYear').drop('Date', axis=1))

    df_out = reduce(lambda a, b: a.join(b), dfs[1:], dfs[0]).sort_values('Date', ascending=False)

    df_residual_reg = df_out[['US IG Spread', 'Excess CAPE Yield', 'ACMTP10']].copy()
    df_residual_reg = df_residual_reg[df_residual_reg.notnull().all(axis=1)]
    model = linear_model.LinearRegression()
    model.fit(
        df_residual_reg[['Excess CAPE Yield', 'ACMTP10']].to_numpy(), df_residual_reg[['US IG Spread']].to_numpy()
    )
    residuals = df_residual_reg[['US IG Spread']].to_numpy() - model.predict(df_residual_reg[['Excess CAPE Yield', 'ACMTP10']].to_numpy())

    df_residual_reg['US IG Spread Ex ERPB And Term Premia'] = residuals
    df_out = df_out.join(df_residual_reg)

    for col in [
        'RealGDP', 'RealGDP Annualized Growth 1yr', 'RealGDP Annualized Growth 3yr', 'RealGDP Annualized Growth 5yr'
    ]:
        df_out[col] = df_out[col].fillna(method='bfill')

    df_out.to_csv('erp-macro-factors-time-series.csv')

    return df_out


def main():

    consolidate_time_series()


if __name__ == '__main__':
    main()
