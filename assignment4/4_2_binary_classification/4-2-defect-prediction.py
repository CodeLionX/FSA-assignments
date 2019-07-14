#!/usr/bin/env python3
import argparse
import csv

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.gaussian_process.kernels import RBF
    import numpy as np
except ImportError:
    print("ERROR - this script requires sklearn")
    print("      - install it using pip via 'pip3 install scikit-learn'")
    exit(1)

try:
    import arff
except ImportError:
    print("ERROR - this script requires liac-arff")
    print("      - install it using pip via 'pip3 install setuptools wheel liac-arff'")
    exit(1)

random_seed = 89715348


def read_arff_file(filename):
    data = arff.load(open(filename, 'r'))
    np_data = np.array(data['data'])

    # select, convert and clean features
    features = np_data[:, :-1]
    features = features.astype('float64')
    where_nan = np.isnan(features)
    features[where_nan] = .0

    # select labels
    labels = np_data[:, -1]
    return features, labels


def output_errors(classifier, train_error, prediction_error):
    if classifier == "logistic-regression":
        name = "Logistic regression "
    elif classifier == "support-vector-machine":
        name = "Support vector machine"
    else:
        name = classifier
    print(name, "error report")
    print("train error: {:.0f}%".format(float(train_error)*100))
    print("prediction error: {:.0f}%".format(float(prediction_error)*100))


def output_predictions(y):
    for value in y:
        print(value)


def custom_kernel(sigma=0.5):
    rbf = RBF()
    expo = 1/(sigma**2)
    return lambda X, Y: np.power(rbf(X, Y), expo)


def main(train_file, predict_file, classifier, output_error):
    if classifier == "logistic-regression":
        predictor = LogisticRegression(
            fit_intercept=True,
            solver='liblinear',  # liblinear, saga, lbfgs
            multi_class='auto',
            max_iter=10000,
            random_state=random_seed
        )
    elif classifier == "support-vector-machine":
        predictor = SVC(
            kernel=custom_kernel(sigma=0.5),
            # kernel='rbf',  # synonym to 'gaussian'
            C=1,
            gamma='auto',
            random_state=random_seed
        )
    else:
        print("Unsupported classifier (--type) selected:", classifier)
        exit(1)

    # train
    X, y = read_arff_file(train_file)
    predictor.fit(X, y)

    # predict
    pred_X, pred_y_gold = read_arff_file(predict_file)
    pred_y = predictor.predict(pred_X)

    if output_error:
        # score() returns accuracy
        train_error = 1 - predictor.score(X, y)
        predict_error = 1 - predictor.score(pred_X, pred_y_gold)
        output_errors(classifier, train_error, predict_error)
    else:
        output_predictions(pred_y)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--train',
        help='path to the training dataset',
        required=True
    )
    parser.add_argument('--predict',
        help='path to the training dataset',
        required=True
    )
    parser.add_argument('--type',
        choices=["logistic-regression", "support-vector-machine"],
        default="logistic-regression",
        help='specify type of binary predictor to use'
    )
    parser.add_argument('--output-error-values', '-e',
        action='store_true',
        dest='output_error',
        help='output relative error instead of prediction values'
    )

    args = parser.parse_args()
    main(args.train, args.predict, args.type, args.output_error)
