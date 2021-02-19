# Copyright 2020 The TensorFlow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module implements the radiance-based ray rendering."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from tensorflow_graphics.util import export_api
from tensorflow_graphics.util import shape


def compute_radiance(rgba_values, distances, name=None):
  """Renders the rgba values for points along a ray, as described in ["NeRF Representing Scenes as Neural Radiance Fields for View Synthesis"](https://github.com/bmild/nerf).

  Note:
    In the following, A1 to An are optional batch dimensions.

  Args:
    rgba_values: A tensor of shape `[A1, ..., An, N, 4]`,
      where N are the samples on the ray.
    distances: A tensor of shape `[A1, ..., An, N]` containing the distances
      between the samples, where N are the samples on the ray.
    name: A name for this op. Defaults to "ray_radiance".

  Returns:
    A tensor of shape `[A1, ..., An, 3]` for the estimated rgb values,
    a tensor of shape `[A1, ..., An, 1]` for the estimated density values,
    and a tensor of shape `[A1, ..., An, N]` for the sample weights.
  """

  with tf.compat.v1.name_scope(name, "ray_radiance", [rgba_values, distances]):
    rgba_values = tf.convert_to_tensor(value=rgba_values)
    distances = tf.convert_to_tensor(value=distances)
    distances = tf.expand_dims(distances, -1)

    shape.check_static(
        tensor=rgba_values, tensor_name="rgba_values", has_dim_equals=(-1, 4))
    shape.check_static(
        tensor=rgba_values,
        tensor_name="rgba_values",
        has_rank_greater_than=1)
    shape.check_static(
        tensor=distances,
        tensor_name="distances",
        has_rank_greater_than=1)
    shape.compare_batch_dimensions(
        tensors=(rgba_values, distances),
        tensor_names=("ray_values", "dists"),
        last_axes=-3,
        broadcast_compatible=True)
    shape.compare_dimensions(
        tensors=(rgba_values, distances),
        tensor_names=("ray_values", "dists"),
        axes=-2)

    rgb, sigma_a = tf.split(rgba_values, [3, 1], axis=-1)
    alpha = 1. - tf.exp(-sigma_a * distances)
    alpha = tf.squeeze(alpha, -1)
    weights = alpha * tf.math.cumprod(1. - alpha + 1e-10, -1, exclusive=True)
    rgb_map = tf.reduce_sum(tf.expand_dims(weights, -1) * rgb, -2)
    acc_map = tf.reduce_sum(weights, -1)
    return rgb_map, tf.expand_dims(acc_map, axis=-1), weights

# API contains all public functions and classes.
__all__ = export_api.get_functions_and_classes()
