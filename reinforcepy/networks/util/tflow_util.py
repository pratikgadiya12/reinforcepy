# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# IslandMan93: Some of this code comes from:
# https://github.com/tensorflow/tensorflow/blob/master/tensorflow/examples/tutorials/mnist/mnist_with_summaries.py
# ==============================================================================
import tensorflow as tf
import numpy as np


def nn_layer(input_tensor, shape, layer_name, act, conv, stride=None, variable_summaries=True):
    """Reusable code for making a simple neural net layer.
    It also sets up name scoping so that the resultant graph is easy to read,
    and adds a number of summary ops.
    """
    # Have to use variable scope because we can have multiple networks that need
    # to reuse these weights
    # https://www.tensorflow.org/versions/master/how_tos/variable_scope/index.html
    with tf.variable_scope(layer_name) as scope:
        # This Variable will hold the state of the weights for the layer
        with tf.name_scope('weights'):
            weights, stdv = weight_variable_torch('weights', shape)
            if variable_summaries:
                compute_variable_summaries(weights, layer_name + '/weights')
        with tf.name_scope('biases'):
            biases = bias_variable_torch('biases', shape[-1], stdv)
            if variable_summaries:
                compute_variable_summaries(biases, layer_name + '/biases')
        if conv:
            with tf.name_scope('conv2d'):
                conv_out = tf.nn.conv2d(input_tensor, weights,
                                        strides=[1, stride, stride, 1],
                                        padding='VALID')
                preactivate = tf.nn.bias_add(conv_out, biases)
        else:
            with tf.name_scope('Wx_plus_b'):
                preactivate = tf.matmul(input_tensor, weights) + biases

        tf.histogram_summary(scope._name_scope + 'pre_activations', preactivate)
        if act is not None:
            activations = act(preactivate, name='activation')
            tf.histogram_summary(scope._name_scope + 'activations', activations)
            return activations
        else:
            return preactivate


def compute_variable_summaries(var, name):
    """Attach a lot of summaries to a Tensor."""
    with tf.name_scope('summaries'):
        mean = tf.reduce_mean(var)
        tf.scalar_summary('mean/' + name, mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.scalar_summary('stddev/' + name, stddev)
        tf.scalar_summary('max/' + name, tf.reduce_max(var))
        tf.scalar_summary('min/' + name, tf.reduce_min(var))
        tf.histogram_summary(name, var)


def weight_variable_torch(name, shape, init='xavier', uniform=True):
    # conv
    if len(shape) == 4:
        # comes from https://github.com/torch/nn/blob/master/SpatialConvolution.lua#L38
        # need only width height input in channels
        # [filter_height, filter_width, in_channels, out_channels]
        if init == 'he':
            stdv = np.sqrt(2) * np.sqrt(1. / np.prod(shape[0:3]))
        else:
            stdv = 1. / np.sqrt(np.prod(shape[0:3]))
    elif len(shape) == 2:
        # looks like torch linear only looks at input channels
        # https://github.com/torch/nn/blob/master/Linear.lua#L25
        if init == 'he':
            stdv = np.sqrt(2) * np.sqrt(1. / shape[0])
        else:
            stdv = 1. / np.sqrt(shape[0])

    if uniform:
        weight_tensor = tf.get_variable(name, shape, initializer=tf.random_uniform_initializer(minval=-stdv, maxval=stdv))
    else:
        weight_tensor = tf.get_variable(name, shape, initializer=tf.random_normal_initializer(stddev=stdv))
    return weight_tensor, stdv


def bias_variable_torch(name, shape, stdv):
    bias_tensor = tf.get_variable(name, shape, initializer=tf.random_uniform_initializer(minval=-stdv, maxval=stdv))
    # bias_tensor = tf.get_variable(name, shape, initializer=tf.constant_initializer(0.1), trainable=True)
    return bias_tensor
