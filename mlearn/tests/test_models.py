# coding: utf-8
# Copyright (c) Materials Virtual Lab
# Distributed under the terms of the BSD License.

import os
import json
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd
from pymatgen import Structure
from monty.json import MSONable

from mlearn.models import LinearModel, GaussianProcessRegressionModel


class LinearModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x_train = np.random.rand(10, 2)
        cls.coef = np.random.rand(2)
        cls.intercept = np.random.rand()
        cls.y_train = cls.x_train.dot(cls.coef) + cls.intercept

    def setUp(self):
        class DummyDescriber(MSONable):
            def describe(self, obj):
                pass

            def describe_all(self, n):
                return pd.DataFrame(n)

        self.lm = LinearModel(DummyDescriber())

        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def test_fit_predict(self):
        self.lm.fit(inputs=self.x_train, outputs=self.y_train)
        x_test = np.random.rand(10, 2)
        y_test = x_test.dot(self.coef) + self.intercept
        y_pred = self.lm.predict(x_test)
        np.testing.assert_array_almost_equal(y_test, y_pred)
        np.testing.assert_array_almost_equal(self.coef, self.lm.coef)
        self.assertAlmostEqual(self.intercept, self.lm.intercept)

    def test_evaluate_fit(self):
        self.lm.fit(inputs=self.x_train, outputs=self.y_train)
        y_pred = self.lm.evaluate_fit()
        np.testing.assert_array_almost_equal(y_pred, self.y_train)

    def test_serialize(self):
        json_str = json.dumps(self.lm.as_dict())
        recover = LinearModel.from_dict(json.loads(json_str))
        self.assertIsNotNone(recover)

    def model_save_load(self):
        self.lm.save(os.path.join(self.test_dir, 'test_lm.save'))
        ori = self.lm.model.coef_
        self.lm.load(os.path.join(self.test_dir, 'test_lm.save'))
        loaded = self.lm.model.coef_
        self.assertAlmostEqual(ori, loaded)


class GaussianProcessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.this_dir = os.path.dirname(os.path.abspath(__file__))
        cls.test_dir = tempfile.mkdtemp()

    def setUp(self):
        self.x_train = np.atleast_2d([1., 3., 5., 6., 7., 8.]).T
        self.y_train = (self.x_train * np.sin(self.x_train)).ravel()

        class DummyDescriber():
            def describe(self, obj):
                pass

            def describe_all(self, n):
                return pd.DataFrame(n)

        self.gpr = GaussianProcessRegressionModel(describer=DummyDescriber(),
                                                  kernel_category='RBF')

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.this_dir)
        shutil.rmtree(cls.test_dir)

    def test_fit_predict(self):
        self.gpr.fit(inputs=self.x_train, outputs=self.y_train)
        x_test = np.atleast_2d(np.linspace(0, 9, 1000)).T
        y_test = x_test * np.sin(x_test)
        y_pred, sigma = self.gpr.predict(x_test, return_std=True)
        upper_bound = y_pred + 1.96 * sigma
        lower_bound = y_pred - 1.96 * sigma
        self.assertTrue(np.all([l < y and y < u for u, y, l in zip(upper_bound, y_test, lower_bound)]))


if __name__ == "__main__":
    unittest.main()
