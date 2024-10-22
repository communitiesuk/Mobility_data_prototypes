import pandas as pd


def process_date_col(df_input, date_col):
    df = df_input.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df['year']= df[date_col].dt.year
    df['month']= df[date_col].dt.month
    df['day']= df[date_col].dt.day
    return df

from pandas.errors import ParserError
def datetime_inplace(df):
    """Automatically detect and convert (in place!) each
    dataframe column of datatype 'object' to a datetime just
    when ALL of its non-NaN values can be successfully parsed
    by pd.to_datetime().  Also returns a ref. to df for
    convenient use in an expression.
    """
    for c in df.columns[df.dtypes=='object']: #don't cnvt num
        try:
            df[c]=pd.to_datetime(df[c])
        except (ParserError,ValueError): #Can't cnvrt some
            pass # ...so leave whole column as-is unconverted
    return df