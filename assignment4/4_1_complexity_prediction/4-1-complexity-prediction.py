#!/usr/bin/env python3
import argparse
import sys
import csv

try:
    from sklearn.linear_model import LinearRegression
    import numpy as np
except ImportError:
    print("ERROR - this script requires sklearn")
    print("      - install it using pip via 'pip3 install scikit-learn'")
    exit(1)


def parse_feature_names(train_columns):
    reader = csv.reader(train_columns.split('\n'), delimiter=';')
    return next(reader)


def parse_float(value, default=.0):
    try:
        return float(value)
    except:
        return default


def read_features(filename, feature_names, predict_col=None):
    keys = []
    X = []
    y = []
    with open(filename, 'r', newline='') as file:
        reader = csv.DictReader(file, delimiter=';')
        keyname = reader.fieldnames[0]
        #print("key:", keyname, file=sys.stderr)
        #print("features:", feature_names, file=sys.stderr)
        #print("predict:", predict_col, file=sys.stderr)

        for row in reader:
            keys.append(row[keyname])
            features = [parse_float(row[name]) for name in feature_names]
            X.append(features)

            if predict_col:
                # we are reading the training file
                y.append(
                    parse_float(row[predict_col])
                )
    X = np.array(X, dtype=np.float64)
    y = np.array(y, dtype=np.float64)

    if predict_col:
        return (keys, X, y)
    else:
        return (keys, X)


def print_output(keys, y):
    writer = csv.writer(sys.stdout, delimiter=';')
    for out in zip(keys, y):
        writer.writerow(out)


def main(train_file, feature_names, predict_file, predict_col):
    predictor = LinearRegression(
        fit_intercept=True,
        n_jobs=-1
    )
    # train
    _, X, y = read_features(train_file, feature_names, predict_col)
    predictor.fit(X, y)
    train_y = predictor.predict(X)
    print("train error:", predictor.score(X, y), file=sys.stderr)

    # predict
    keys, pred_X = read_features(predict_file, feature_names)
    pred_y = predictor.predict(pred_X)

    print(
        "prediction error (to assignment)",
        predictor.score(pred_X, [33, 12, 17]),
        file=sys.stderr
    )
    print_output(keys, pred_y)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--train',
        help='path to the training dataset',
        required=True
    )
    parser.add_argument('--train-columns',
        help='select columns used as features (csv-string)',
        required=True
    )
    parser.add_argument('--predict',
        help='path to the training dataset',
        required=True
    )
    parser.add_argument('--prediction-column',
        help='select prediction column',
        required=True
    )

    args = parser.parse_args()
    feature_names = parse_feature_names(args.train_columns)
    main(args.train, feature_names, args.predict, args.prediction_column)
