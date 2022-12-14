import os
import sys
import pandas as pd
from sqlalchemy import create_engine


def load_data(messages_filepath: str, categories_filepath: str) -> pd.DataFrame:
    """ load messages and categories form specified paths

    Args:
        messages_filepath: filepath to messages
        categories_filepath: filepath to categories

    Returns:
        merges dataframe
    """
    messages = pd.read_csv(messages_filepath)
    categories = pd.read_csv(categories_filepath)
    # merge datasets
    return messages.merge(categories, on='id', how='left').drop('id', axis=1)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data by extending categories and encoding them, removing duplicates

    Args:
        df: dataframe containing categorized messages

    Returns:
        cleaned dataframe of categorized messages in one hot encoding
    """
    # split categories into separate category columns
    categories = df['categories'].str.split(";", expand=True)

    # select the first row of the categories
    row = categories.iloc[0, :]
    # use this row to extract a list of new column names for categories.
    # one way is to apply a lambda function that takes everything
    # up to the second to last character of each string with slicing
    category_colnames = row.apply(lambda x: x[:-2])
    # rename the columns of `categories`
    categories.columns = category_colnames

    # convert category values to just numbers 0 or 1
    # iterate through the category columns in df to keep only the last character of each string (the 1 or 0)
    for column in categories:
        categories[column] = categories[column].str[-1:]  # set each value to be the last character of the string
        categories[column] = categories[column].astype(int)  # convert column from string to numeric
    # as there are entries of '2' in column 'related', which go back the original value of 'related-2', these will be replaced by the value '1'
    categories['related'] = categories['related'].apply(lambda x: x if x in [0,1] else 1)

    # replace categories column in df with new category columns
    df.drop('categories', axis=1, inplace=True)  # drop the original categories column from `df`
    df = pd.concat([df, categories], axis=1)  # concatenate the original dataframe with the new `categories` dataframe

    # drop duplicates
    df = df.drop_duplicates()

    return df


def save_data(df, database_filename):
    base = 'sqlite:///'
    path = os.path.join(base, database_filename)
    engine = create_engine(path)
    df.to_sql('messages', engine, index=False, if_exists='replace')


def main():
    if len(sys.argv) == 4:

        messages_filepath, categories_filepath, database_filepath = sys.argv[1:]

        print('Loading data...\n    MESSAGES: {}\n    CATEGORIES: {}'
              .format(messages_filepath, categories_filepath))
        df = load_data(messages_filepath, categories_filepath)

        print('Cleaning data...')
        df = clean_data(df)
        
        print('Saving data...\n    DATABASE: {}'.format(database_filepath))
        save_data(df, database_filepath)
        
        print('Cleaned data saved to database!')
    
    else:
        print('Please provide the filepaths of the messages and categories '\
              'datasets as the first and second argument respectively, as '\
              'well as the filepath of the database to save the cleaned data '\
              'to as the third argument. \n\nExample: python process_data.py '\
              'disaster_messages.csv disaster_categories.csv '\
              'DisasterResponse.db')


if __name__ == '__main__':
    main()
