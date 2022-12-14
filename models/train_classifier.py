"""A ML pipeline that outputs a model to classify the message into categories."""

import pickle
import sys

import nltk
import pandas as pd

nltk.download("punkt")
nltk.download("wordnet")
nltk.download("omw-1.4")

from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sqlalchemy import create_engine


def load_data(database_filepath):
    """Load data from sqlite database and return ."""

    # create slqlite engine
    engine = create_engine(f"sqlite:///{database_filepath}")

    # read in dataframe
    df = pd.read_sql_table("messages_categories", engine)

    # define features and label arrays
    X = df["message"].values
    Y = df.iloc[:, 4:].values
    category_names = df.columns[4:]

    # check that Y contains 36 categories
    assert Y.shape[1] == len(category_names) == 36, "Y does not contain 36 categories"

    return X, Y, category_names


def tokenize(text):
    """Tokenize string of text and return tokenized words."""

    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(text.lower())

    return [lemmatizer.lemmatize(t).strip() for t in tokens]


def build_model():
    """Build model pipeline and return gridsearch object."""
    # text processing and model pipeline
    pipeline = Pipeline(
        [
            (
                "vect",
                CountVectorizer(
                    strip_accents="unicode", analyzer="word", tokenizer=tokenize
                ),
            ),
            ("tifd", TfidfTransformer()),
            ("clf", MultiOutputClassifier(RandomForestClassifier(random_state=85055))),
        ]
    )

    # define parameters for grid search
    parameters = {
        "tifd__use_idf": [True, False],
        "clf__estimator__n_estimators": [10, 100],
    }

    # create gridsearch object and return as final model pipeline
    cv = GridSearchCV(pipeline, param_grid=parameters)

    return cv


def evaluate_model(model, X_test, Y_test, category_names):
    """Predict Y test array and print classification report."""
    Y_pred = model.predict(X_test)
    print(classification_report(Y_test, Y_pred, target_names=category_names))


def save_model(model, model_filepath):
    """Export model as a pickle file."""
    # pickle.dump(model.best_estimator_, open(model_filepath, 'wb'))
    pickle.dump(model, open(model_filepath, "wb"))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print("Loading data...\n    DATABASE: {}".format(database_filepath))
        X, Y, category_names = load_data(database_filepath)
        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=0.2, random_state=85055
        )

        print("Building model...")
        model = build_model()

        print("Training model...")
        model.fit(X_train, Y_train)

        print("Evaluating model...")
        evaluate_model(model, X_test, Y_test, category_names)

        print("Saving model...\n    MODEL: {}".format(model_filepath))
        save_model(model, model_filepath)

        print("Trained model saved!")

    else:
        print(
            "Please provide the filepath of the disaster messages database "
            "as the first argument and the filepath of the pickle file to "
            "save the model to as the second argument. \n\nExample: python "
            "train_classifier.py ../data/DisasterResponse.db classifier.pkl"
        )


if __name__ == "__main__":
    main()
