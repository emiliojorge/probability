# Copyright 2018 The TensorFlow Probability Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Tests for initializers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


# Dependency imports
import numpy as np
from scipy import stats as sp_stats

import tensorflow as tf
import tensorflow_probability as tfp

from tensorflow_probability.python.distributions import exponential as exponential_lib

from tensorflow_probability.python.internal import test_util as tfp_test_util
tfd = tfp.distributions
from tensorflow.python.framework import test_util  # pylint: disable=g-direct-tensorflow-import,g-import-not-at-top


@test_util.run_all_in_graph_and_eager_modes
class ExponentialTest(tf.test.TestCase):

  def testExponentialLogPDF(self):
    batch_size = 6
    lam = tf.constant([2.0] * batch_size)
    lam_v = 2.0
    x = np.array([2.5, 2.5, 4.0, 0.1, 1.0, 2.0], dtype=np.float32)
    exponential = exponential_lib.Exponential(rate=lam)

    log_pdf = exponential.log_prob(x)
    self.assertEqual(log_pdf.shape, (6,))

    pdf = exponential.prob(x)
    self.assertEqual(pdf.shape, (6,))

    expected_log_pdf = sp_stats.expon.logpdf(x, scale=1 / lam_v)
    self.assertAllClose(self.evaluate(log_pdf), expected_log_pdf)
    self.assertAllClose(self.evaluate(pdf), np.exp(expected_log_pdf))

  def testExponentialLogPDFBoundary(self):
    # Check that Log PDF is finite at 0.
    rate = np.array([0.1, 0.5, 1., 2., 5., 10.], dtype=np.float32)
    exponential = exponential_lib.Exponential(rate=rate)
    log_pdf = exponential.log_prob(0.)
    self.assertAllClose(np.log(rate), self.evaluate(log_pdf))

  def testExponentialCDF(self):
    batch_size = 6
    lam = tf.constant([2.0] * batch_size)
    lam_v = 2.0
    x = np.array([2.5, 2.5, 4.0, 0.1, 1.0, 2.0], dtype=np.float32)

    exponential = exponential_lib.Exponential(rate=lam)

    cdf = exponential.cdf(x)
    self.assertEqual(cdf.shape, (6,))

    expected_cdf = sp_stats.expon.cdf(x, scale=1 / lam_v)
    self.assertAllClose(self.evaluate(cdf), expected_cdf)

  def testExponentialLogSurvival(self):
    batch_size = 7
    lam = tf.constant([2.0] * batch_size)
    lam_v = 2.0
    x = np.array([2.5, 2.5, 4.0, 0.1, 1.0, 2.0, 10.0], dtype=np.float32)

    exponential = exponential_lib.Exponential(rate=lam)

    log_survival = exponential.log_survival_function(x)
    self.assertEqual(log_survival.shape, (7,))

    expected_log_survival = sp_stats.expon.logsf(x, scale=1 / lam_v)
    self.assertAllClose(self.evaluate(log_survival), expected_log_survival)

  def testExponentialMean(self):
    lam_v = np.array([1.0, 4.0, 2.5])
    exponential = exponential_lib.Exponential(rate=lam_v)
    self.assertEqual(exponential.mean().shape, (3,))
    expected_mean = sp_stats.expon.mean(scale=1 / lam_v)
    self.assertAllClose(self.evaluate(exponential.mean()), expected_mean)

  def testExponentialVariance(self):
    lam_v = np.array([1.0, 4.0, 2.5])
    exponential = exponential_lib.Exponential(rate=lam_v)
    self.assertEqual(exponential.variance().shape, (3,))
    expected_variance = sp_stats.expon.var(scale=1 / lam_v)
    self.assertAllClose(
        self.evaluate(exponential.variance()), expected_variance)

  def testExponentialEntropy(self):
    lam_v = np.array([1.0, 4.0, 2.5])
    exponential = exponential_lib.Exponential(rate=lam_v)
    self.assertEqual(exponential.entropy().shape, (3,))
    expected_entropy = sp_stats.expon.entropy(scale=1 / lam_v)
    self.assertAllClose(self.evaluate(exponential.entropy()), expected_entropy)

  def testExponentialSample(self):
    lam = tf.constant([3.0, 4.0])
    lam_v = [3.0, 4.0]
    n = tf.constant(100000)
    exponential = exponential_lib.Exponential(rate=lam)

    samples = exponential.sample(n, seed=tfp_test_util.test_seed())
    sample_values = self.evaluate(samples)
    self.assertEqual(sample_values.shape, (100000, 2))
    self.assertFalse(np.any(sample_values < 0.0))
    for i in range(2):
      self.assertLess(
          sp_stats.kstest(sample_values[:, i],
                          sp_stats.expon(scale=1.0 / lam_v[i]).cdf)[0], 0.01)

  def testExponentialSampleMultiDimensional(self):
    batch_size = 2
    lam_v = [3.0, 22.0]
    lam = tf.constant([lam_v] * batch_size)

    exponential = exponential_lib.Exponential(rate=lam)

    n = 100000
    samples = exponential.sample(n, seed=tfp_test_util.test_seed())
    self.assertEqual(samples.shape, (n, batch_size, 2))

    sample_values = self.evaluate(samples)

    self.assertFalse(np.any(sample_values < 0.0))
    for i in range(2):
      self.assertLess(
          sp_stats.kstest(sample_values[:, 0, i],
                          sp_stats.expon(scale=1.0 / lam_v[i]).cdf)[0], 0.01)
      self.assertLess(
          sp_stats.kstest(sample_values[:, 1, i],
                          sp_stats.expon(scale=1.0 / lam_v[i]).cdf)[0], 0.01)

  def testFullyReparameterized(self):
    lam = tf.constant([0.1, 1.0])
    _, grad_lam = tfp.math.value_and_gradient(
        lambda l: exponential_lib.Exponential(rate=lam).sample(100), lam)
    self.assertIsNotNone(grad_lam)

  def testExponentialExponentialKL(self):
    a_rate = np.arange(0.5, 1.6, 0.1)
    b_rate = np.arange(0.5, 1.6, 0.1)

    # This reshape is intended to expand the number of test cases.
    a_rate = a_rate.reshape((len(a_rate), 1))
    b_rate = b_rate.reshape((1, len(b_rate)))

    a = exponential_lib.Exponential(rate=a_rate)
    b = exponential_lib.Exponential(rate=b_rate)

    # Consistent with
    # http://www.mast.queensu.ca/~communications/Papers/gil-msc11.pdf, page 108
    true_kl = np.log(a_rate) - np.log(b_rate) + (b_rate - a_rate) / a_rate

    kl = tfd.kl_divergence(a, b)

    x = a.sample(int(4e5), seed=tfp_test_util.test_seed())
    kl_sample = tf.reduce_mean(
        input_tensor=a.log_prob(x) - b.log_prob(x), axis=0)

    kl_, kl_sample_ = self.evaluate([kl, kl_sample])
    self.assertAllClose(true_kl, kl_, atol=0., rtol=1e-12)
    self.assertAllClose(true_kl, kl_sample_, atol=0., rtol=8e-2)

    zero_kl = tfd.kl_divergence(a, a)
    true_zero_kl_, zero_kl_ = self.evaluate([tf.zeros_like(zero_kl), zero_kl])
    self.assertAllEqual(true_zero_kl_, zero_kl_)


if __name__ == "__main__":
  tf.test.main()
