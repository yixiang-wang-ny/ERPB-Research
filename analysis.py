import pandas as pd
from abc import ABC, abstractmethod


def get_data():

    return pd.read_csv('erp-macro-factors-time-series.csv')


class Sampler(ABC):

    dependent_variable = 'Excess CAPE Yield'
    group_col_name = 'group'

    @abstractmethod
    def _divide(self, df, feature) -> pd.DataFrame:
        return pd.DataFrame()

    def divide(self, df, feature) -> pd.DataFrame:

        df = df[df[feature].notnull()]
        df_divided = self._divide(df.copy(), feature)

        return df_divided[
            ['MonthYear', 'Date', self.dependent_variable, feature, self.group_col_name]
        ].set_index('MonthYear')


class EqualSizeSampler(Sampler):

    def __init__(self, q: int):
        self.q = q

    def _divide(self, df, feature) -> pd.DataFrame:

        return


class BooleanSampler(Sampler):

    def _divide(self, df, feature) -> pd.DataFrame:

        df[self.group_col_name] = df[feature]

        return df


def feature_basic_analysis(df, feature_name):

    return df


def feature_single_variable_regression_analysis(df, feature_name):

    return df


def feature_buckets_analysis(df, feature_name, sampler: Sampler):

    df_grouped = sampler.divide(df, feature_name)

    return df_grouped


def main():

    df = get_data()

    feature_buckets_analysis(df, 'CPI Change', EqualSizeSampler(4))

    return


if __name__ == '__main__':
    main()


