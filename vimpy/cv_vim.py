## Python class for cross-validated estimates of variable importance
## compute estimates and confidence intervals, do hypothesis testing

## import required libraries
import numpy as np
from scipy.stats import norm
from .predictiveness_measures import cv_predictiveness
from .vimpy_utils import get_measure_function


class cv_vim:

    ## define initialization values
    """
    @param y the outcome
    @param x the feature data
    @param s the feature group of interest
    @param measure_type the predictiveness measure to use (for now, one of "r_squared", "auc", "accuracy", "deviance")
    @param V the number of cross-validation folds (defaults to 5)
    @param pred_func the function that predicts outcome given features
    @param f fitted values from regression of outcome on all features (only used if pred_func is not specified)
    @param r fitted values from regression of outcome on reduced set of features (only used if pred_func is not specified)
    @param na_rm remove NAs prior to computing predictiveness? (defaults to False)
    """
    def __init__(self, y, x, s, measure_type, V = 5, pred_func = None, f = None, r = None, na_rm = False):
        self.y_ = y
        self.x_ = x
        self.s_ = s
        self.n_ = y.shape[0]
        self.p_ = x.shape[1]
        self.pred_func_ = pred_func
        self.f_ = f
        self.r_ = r
        assert (pred_func is not None or (f is not None and r is not None))
        self.V_ = V
        self.measure_type_ = measure_type
        self.measure_ = get_measure_function(measure_type)
        self.ic_ = []
        self.vimp_ = []
        self.se_ = []
        self.ci_ = []
        self.hyp_test_ = []
        self.test_statistic_ = []
        self.p_value_ = []
        self.v_full_ = []
        self.preds_full_ = []
        self.ic_full_ = []
        self.v_redu_ = []
        self.preds_redu_ = []
        self.ic_redu_ = []
        self.se_full_ = []
        self.se_redu_ = []
        self.ci_full_ = []
        self.ci_redu_ = []
        ## set up outer folds for hypothesis testing
        self.folds_outer_ = np.random.choice(a = np.arange(2), size = self.n_, replace = True, p = np.array([0.5, 0.5]))
        ## if only two unique values in y, assume binary
        self.binary_ = (np.unique(y).shape[0] == 2)
        self.na_rm_ = na_rm

    ## calculate the plug-in estimator
    def get_point_est(self):
        self.v_full_, self.preds_full_, self.ic_full_ = cv_predictiveness(self.x_[self.folds_outer_ == 1, :], self.y_[self.folds_outer_ == 1], np.arange(self.p_), self.measure_, self.pred_func_, V = self.V_, stratified = self.binary_, na_rm = self.na_rm_)
        self.v_redu_, self.preds_redu_, self.ic_redu_ = cv_predictiveness(self.x_[self.folds_outer_ == 0, :], self.y_[self.folds_outer_ == 0], np.arange(self.p_).delete(self.s_), self.measure_, self.pred_func_, V = self.V_, stratified = self.binary_, na_rm = self.na_rm_)
        self.vimp_ = self.v_full_ - self.v_redu_
        return self

    ## calculate the influence function
    def get_influence_function(self):
        self.ic_ = self.ic_full_ - self.ic_redu_
        return self

    ## calculate the standard error
    def get_se(self):
        self.se_full_ = np.sqrt(np.mean(self.ic_full_ ** 2)) / np.sqrt(self.ic_full_.shape[0])
        self.se_redu_ = np.sqrt(np.mean(self.ic_redu_ ** 2)) / np.sqrt(self.ic_redu_.shape[0])
        self.se_ = np.sqrt(np.mean(self.ic_ ** 2)) / np.sqrt(self.ic_.shape[0])
        return self

    ## calculate the ci based on the estimate and the standard error
    def get_ci(self, level = 0.95):
        ## get alpha from the level
        a = (1 - level)/2.
        a = np.array([a, 1 - a])
        ## calculate the quantiles
        fac = norm.ppf(a)
        ## set up the ci array
        ci = np.zeros((self.vimp_.shape[0], 2))
        ## create cis for vimp, predictiveness
        self.ci_ = self.vimp_ + np.outer((self.se_), fac)
        self.ci_full_ = self.v_full_ + np.outer((self.se_full_), fac)
        self.ci_redu_ = self.v_redu_ + np.outer((self.se_redu_), fac)
        return self

    ## do a hypothesis test
    def hypothesis_test(self, alpha = 0.05, delta = 0):
        self.test_statistic_ = (self.v_full_ - self.v_redu_ - delta) / np.sqrt(self.se_full_ ** 2 + self.se_redu_ ** 2)
        self.p_value_ = 1 - norm.ppf(self.test_statistic_)
        self.hyp_test_ = self.p_value_ < alpha
        return(self)
