import pandas as pd
from abc import ABC, abstractmethod
import statsmodels.api as sm
from collections import namedtuple
from typing import Optional, List


def get_data():

    return pd.read_csv('erp-macro-factors-time-series.csv')


class Bucket(ABC):

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


class QuantileBucket(Bucket):

    def __init__(self, q: int):
        self.q = q

    def _divide(self, df, feature) -> pd.DataFrame:

        df[self.group_col_name] = pd.qcut(df[feature], self.q)
        return df


class BooleanBucket(Bucket):

    def _divide(self, df, feature) -> pd.DataFrame:

        df[self.group_col_name] = df[feature]

        return df


BucketRange = namedtuple('BucketRange', ('low', 'high'))


class CustomizedRangeBucket(Bucket):

    def __init__(self, ranges: List[BucketRange], range_names: Optional[List[str]] = None):
        self.ranges = ranges
        if range_names is None:
            range_names = [f'{r.low} to {r.high}' for r in self.ranges]
        self.range_names = range_names

    def _get_range(self, x):

        for r, name in zip(self.ranges, self.range_names):
            if r.low < x <= r.high:
                return name

        return None

    def _divide(self, df, feature) -> pd.DataFrame:

        df[self.group_col_name] = df[feature].apply(self._get_range)
        df = df[df[self.group_col_name].notnull()]

        return df


def analysis(df, bucket, feature):
    df_grouped = bucket.divide(df, feature)

    try:
        df_grouped_scatter = df_grouped.copy()
        df_grouped_scatter[feature] = df_grouped_scatter[feature].apply(float)
        df_grouped_scatter.plot.scatter(x=feature, y='Excess CAPE Yield', )
    except:
        print('Scatter failed probably due to non numerical feature value')

    try:
        mod = sm.OLS(df_grouped['Excess CAPE Yield'], df_grouped[feature])
        res = mod.fit()
        print(res.summary())
    except:
        print('Scatter failed probably due to non numerical feature value')

    # buckets
    print()
    print('Bucket Basic Stats:')
    print(df_grouped.groupby('group')['Excess CAPE Yield'].describe())
    df_grouped[['Excess CAPE Yield', 'group']].boxplot(by="group")


def main():

    df = get_data()
    bucket = QuantileBucket(4)
    feature = 'Fed Fund Effective Rate'

    analysis(df, bucket, feature)

    df = get_data()
    bucket = BooleanBucket()
    feature = 'In Recession'

    analysis(df, bucket, feature)

    df = get_data()
    bucket = CustomizedRangeBucket(
        ranges=[BucketRange(low=0, high=5), BucketRange(low=5, high=10), BucketRange(low=10, high=15)]
    )
    feature = 'Unemployment Rate'

    analysis(df, bucket, feature)


    return


if __name__ == '__main__':
    main()


