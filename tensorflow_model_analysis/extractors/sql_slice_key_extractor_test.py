# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for tensorflow_model_analysis.google.extractors.sql_slice_key_extractor."""

import apache_beam as beam
from apache_beam.testing import util
import pyarrow as pa
import tensorflow as tf
from tensorflow_model_analysis import constants
from tensorflow_model_analysis.api import model_eval_lib
from tensorflow_model_analysis.eval_saved_model import testutil
from tensorflow_model_analysis.extractors import sql_slice_key_extractor
from tensorflow_model_analysis.proto import config_pb2
from tfx_bsl.tfxio import tf_example_record

from google.protobuf import text_format
from tensorflow_metadata.proto.v0 import schema_pb2

_SCHEMA = text_format.Parse(
    """
        feature {
          name: "fixed_int"
          type: INT
        }
        feature {
          name: "fixed_float"
          type: FLOAT
        }
        feature {
          name: "fixed_string"
          type: BYTES
        }
        """, schema_pb2.Schema())


class SqlSliceKeyExtractorTest(testutil.TensorflowModelAnalysisTest):

  def testSqlSliceKeyExtractor(self):
    eval_config = config_pb2.EvalConfig(slicing_specs=[
        config_pb2.SlicingSpec(slice_keys_sql="""
        SELECT
          STRUCT(fixed_string)
        FROM
          example.fixed_string,
          example.fixed_int
        WHERE fixed_int = 1
        """)
    ])
    slice_key_extractor = sql_slice_key_extractor.SqlSliceKeyExtractor(
        eval_config)

    tfx_io = tf_example_record.TFExampleBeamRecord(
        physical_format='inmem',
        telemetry_descriptors=['test', 'component'],
        schema=_SCHEMA,
        raw_record_column_name=constants.ARROW_INPUT_COLUMN)
    examples = [
        self._makeExample(
            fixed_int=1, fixed_float=1.0, fixed_string='fixed_string1'),
        self._makeExample(
            fixed_int=1, fixed_float=1.0, fixed_string='fixed_string2'),
        self._makeExample(
            fixed_int=2, fixed_float=0.0, fixed_string='fixed_string3')
    ]

    with beam.Pipeline() as pipeline:
      # pylint: disable=no-value-for-parameter
      result = (
          pipeline
          | 'Create' >> beam.Create([e.SerializeToString() for e in examples],
                                    reshuffle=False)
          | 'BatchExamples' >> tfx_io.BeamSource(batch_size=3)
          | 'InputsToExtracts' >> model_eval_lib.BatchedInputsToExtracts()
          | slice_key_extractor.stage_name >> slice_key_extractor.ptransform)

      # pylint: enable=no-value-for-parameter

      def check_result(got):
        try:
          self.assertLen(got, 1)
          self.assertEqual(got[0][constants.SLICE_KEY_TYPES_KEY],
                           [[(('fixed_string', 'fixed_string1'),)],
                            [(('fixed_string', 'fixed_string2'),)], []])

        except AssertionError as err:
          raise util.BeamAssertException(err)

      util.assert_that(result, check_result)

  def testSqlSliceKeyExtractorWithCrossSlices(self):
    eval_config = config_pb2.EvalConfig(slicing_specs=[
        config_pb2.SlicingSpec(slice_keys_sql="""
        SELECT
          STRUCT(fixed_string, fixed_int)
        FROM
          example.fixed_string,
          example.fixed_int
        WHERE fixed_int = 1
        """)
    ])
    slice_key_extractor = sql_slice_key_extractor.SqlSliceKeyExtractor(
        eval_config)

    tfx_io = tf_example_record.TFExampleBeamRecord(
        physical_format='inmem',
        telemetry_descriptors=['test', 'component'],
        schema=_SCHEMA,
        raw_record_column_name=constants.ARROW_INPUT_COLUMN)
    examples = [
        self._makeExample(
            fixed_int=1, fixed_float=1.0, fixed_string='fixed_string1'),
        self._makeExample(
            fixed_int=1, fixed_float=1.0, fixed_string='fixed_string2'),
        self._makeExample(
            fixed_int=2, fixed_float=0.0, fixed_string='fixed_string3')
    ]

    with beam.Pipeline() as pipeline:
      # pylint: disable=no-value-for-parameter
      result = (
          pipeline
          | 'Create' >> beam.Create([e.SerializeToString() for e in examples],
                                    reshuffle=False)
          | 'BatchExamples' >> tfx_io.BeamSource(batch_size=3)
          | 'InputsToExtracts' >> model_eval_lib.BatchedInputsToExtracts()
          | slice_key_extractor.stage_name >> slice_key_extractor.ptransform)

      # pylint: enable=no-value-for-parameter

      def check_result(got):
        try:
          self.assertLen(got, 1)
          self.assertEqual(got[0][constants.SLICE_KEY_TYPES_KEY], [[
              (('fixed_string', 'fixed_string1'), ('fixed_int', '1'))
          ], [(('fixed_string', 'fixed_string2'), ('fixed_int', '1'))], []])

        except AssertionError as err:
          raise util.BeamAssertException(err)

      util.assert_that(result, check_result)

  def testSqlSliceKeyExtractorWithEmptySqlConfig(self):
    eval_config = config_pb2.EvalConfig()
    slice_key_extractor = sql_slice_key_extractor.SqlSliceKeyExtractor(
        eval_config)

    tfx_io = tf_example_record.TFExampleBeamRecord(
        physical_format='inmem',
        telemetry_descriptors=['test', 'component'],
        schema=_SCHEMA,
        raw_record_column_name=constants.ARROW_INPUT_COLUMN)
    examples = [
        self._makeExample(
            fixed_int=1, fixed_float=1.0, fixed_string='fixed_string1'),
        self._makeExample(
            fixed_int=1, fixed_float=1.0, fixed_string='fixed_string2'),
        self._makeExample(
            fixed_int=2, fixed_float=0.0, fixed_string='fixed_string3')
    ]

    with beam.Pipeline() as pipeline:
      # pylint: disable=no-value-for-parameter
      result = (
          pipeline
          | 'Create' >> beam.Create([e.SerializeToString() for e in examples],
                                    reshuffle=False)
          | 'BatchExamples' >> tfx_io.BeamSource(batch_size=3)
          | 'InputsToExtracts' >> model_eval_lib.BatchedInputsToExtracts()
          | slice_key_extractor.stage_name >> slice_key_extractor.ptransform)

      # pylint: enable=no-value-for-parameter

      def check_result(got):
        try:
          self.assertLen(got, 1)
          self.assertEqual(got[0][constants.SLICE_KEY_TYPES_KEY], [[], [], []])

        except AssertionError as err:
          raise util.BeamAssertException(err)

      util.assert_that(result, check_result)

  def testSqlSliceKeyExtractorWithMultipleSchema(self):
    eval_config = config_pb2.EvalConfig(slicing_specs=[
        config_pb2.SlicingSpec(slice_keys_sql="""
        SELECT
          STRUCT(fixed_string)
        FROM
          example.fixed_string,
          example.fixed_int
        WHERE fixed_int = 1
        """)
    ])
    slice_key_extractor = sql_slice_key_extractor.SqlSliceKeyExtractor(
        eval_config)

    record_batch_1 = pa.RecordBatch.from_arrays([
        pa.array([[1], [1], [2]], type=pa.list_(pa.int64())),
        pa.array([[1.0], [1.0], [2.0]], type=pa.list_(pa.float64())),
        pa.array([['fixed_string1'], ['fixed_string2'], ['fixed_string3']],
                 type=pa.list_(pa.string())),
    ], ['fixed_int', 'fixed_float', 'fixed_string'])
    record_batch_2 = pa.RecordBatch.from_arrays([
        pa.array([[1], [1], [2]], type=pa.list_(pa.int64())),
        pa.array([[1.0], [1.0], [2.0]], type=pa.list_(pa.float64())),
        pa.array([['fixed_string1'], ['fixed_string2'], ['fixed_string3']],
                 type=pa.list_(pa.string())),
        pa.array([['extra_field1'], ['extra_field2'], ['extra_field3']],
                 type=pa.list_(pa.string())),
    ], ['fixed_int', 'fixed_float', 'fixed_string', 'extra_field'])

    with beam.Pipeline() as pipeline:
      # pylint: disable=no-value-for-parameter
      result = (
          pipeline
          | 'Create' >> beam.Create([record_batch_1, record_batch_2],
                                    reshuffle=False)
          | 'InputsToExtracts' >> model_eval_lib.BatchedInputsToExtracts()
          | slice_key_extractor.stage_name >> slice_key_extractor.ptransform)

      # pylint: enable=no-value-for-parameter

      def check_result(got):
        try:
          self.assertLen(got, 2)
          self.assertEqual(got[0][constants.SLICE_KEY_TYPES_KEY],
                           [[(('fixed_string', 'fixed_string1'),)],
                            [(('fixed_string', 'fixed_string2'),)], []])
          self.assertEqual(got[1][constants.SLICE_KEY_TYPES_KEY],
                           [[(('fixed_string', 'fixed_string1'),)],
                            [(('fixed_string', 'fixed_string2'),)], []])

        except AssertionError as err:
          raise util.BeamAssertException(err)

      util.assert_that(result, check_result)


if __name__ == '__main__':
  tf.test.main()
