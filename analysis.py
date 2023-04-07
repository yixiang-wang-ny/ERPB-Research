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

        df = df[df[feature].notnull() & df[self.dependent_variable].notnull()]
        df_divided = self._divide(df.copy(), feature)

        return df_divided[
            ['MonthYear', 'Date', self.dependent_variable, feature, self.group_col_name]
        ].set_index('MonthYear')


class QuantileSampler(Sampler):

    def __init__(self, q: int):
        self.q = q

    def _divide(self, df, feature) -> pd.DataFrame:

        df[self.group_col_name] = pd.qcut(df[feature], self.q)
        return df


class BooleanSampler(Sampler):

    def _divide(self, df, feature) -> pd.DataFrame:

        df[self.group_col_name] = df[feature]

        return df


def main():

    df = get_data()
    sampler = QuantileSampler(4)
    feature = 'Fed Fund Effective Rate'

    df_grouped = sampler.divide(df, feature)

    df_grouped.plot.scatter(x='Fed Fund Effective Rate', y='Excess CAPE Yield', )

    print(df_grouped.groupby('group')['Excess CAPE Yield'].describe())
    df_grouped[['Excess CAPE Yield', 'group']].boxplot(by="group")

    return


if __name__ == '__main__':
    main()


