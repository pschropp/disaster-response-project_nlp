import os
import sys
import nltk

nltk.download(['punkt', 'wordnet', 'averaged_perceptron_tagger'])
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

import numpy as np
import pandas as pd
from sqlalchemy import create_engine

from typing import Tuple, List, Any, Optional, Dict, Union

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib


def load_data(database_filepath: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """ Load and prepare data from sql db

    Args:
        database_filepath: path to db file including .db extension

    Returns:
        X and Y vectors as well as category names
    """
    base = 'sqlite:///'
    path = os.path.join(base, database_filepath)
    engine = create_engine(path)
    df = pd.read_sql_table('messages', engine)
    X = df['message'].values
    y_df = df.drop(['message', 'original', 'genre'], axis=1)
    Y = y_df.values
    return X, Y, y_df.columns


def tokenize(text: str) -> List[str]:
    """ Tokenize string

Args:
    text: text to tokenize

Returns:
    list of tokenized strings
"""
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()

    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)

    return clean_tokens


def build_model(classifier: Any = RandomForestClassifier(),
                grid_search_parameters: Optional[Dict[str, List[str]]] = None) -> Union[Pipeline, GridSearchCV]:
    """ Build model based on parameters.

    As default, a random forest classifier is used. Grid search will be performed, if a parameter list for grid search
    is passed (default being no gridsearch).

    Returns:
        model
    """
    pipeline = Pipeline([
        ('vect', CountVectorizer(tokenizer=tokenize)),
        ('tfidf', TfidfTransformer()),
        ('clf', MultiOutputClassifier(classifier))
    ])

    if grid_search_parameters:
        model = GridSearchCV(pipeline, param_grid=grid_search_parameters, n_jobs=-1, verbose=3)
    else:
        model = pipeline

    return model


def evaluate_model(model: Any, X_test: List[str], Y_test: List[str], category_names: List[str]) -> None:
    """ Predict values and print model scores

    Args:
        model: pipeline
        X_test: messages
        Y_test: categories
        category_names: list of category names

    Returns:
        None
    """
    y_pred = model.predict(X_test)

    y_test_df = pd.DataFrame(Y_test, columns=category_names)
    y_pred_df = pd.DataFrame(y_pred, columns=category_names)
    for col in y_test_df.columns:
        print(classification_report(y_test_df[col], y_pred_df[col]))


def save_model(model: Any, model_filepath: str) -> None:
    """ Save model as pickle file

    Args:
        model: pipeline to save
        model_filepath: path including .pkl extension

    Returns:
        None
    """
    joblib.dump(model, model_filepath, compress=1)


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2)

        print('Building model...')
        grid_search_param = {"clf__estimator__max_features": ["sqrt", "log2"]}
        model = build_model(grid_search_parameters=grid_search_param)

        print('Training model...')
        model.fit(X_train, Y_train)

        print('Evaluating model...')
        evaluate_model(model, X_test, Y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '
              'as the first argument and the filepath of the pickle file to '
              'save the model to as the second argument. \n\nExample: python '
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()
