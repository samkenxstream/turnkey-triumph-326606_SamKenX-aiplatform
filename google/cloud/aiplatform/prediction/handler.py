# -*- coding: utf-8 -*-

# Copyright 2022 Google LLC
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
#

from typing import Optional, Type

try:
    from fastapi import Request
    from fastapi import Response
except ImportError:
    raise ImportError(
        "FastAPI is not installed and is required to build model servers. "
        'Please install the SDK using "pip install python-aiplatform[prediction]"'
    )

from google.cloud.aiplatform.prediction import handler_utils
from google.cloud.aiplatform.prediction.predictor import Predictor
from google.cloud.aiplatform.prediction.serializer import DefaultSerializer


class Handler:
    """Interface for Handler class to handle prediction requests."""

    def __init__(
        self, gcs_artifacts_uri: str, predictor: Optional[Type[Predictor]] = None,
    ):
        """Initializes a Handler instance.

        Args:
            gcs_artifacts_uri (str):
                Required. The value of the environment variable AIP_STORAGE_URI.
            predictor (Type[Predictor]):
                Optional. The Predictor class this handler uses to initiate predictor
                instance if given.
        """
        pass

    def handle(self, request: Request) -> Response:
        """Handles a prediction request.

        Args:
            request (Request):
                The request sent to the application.

        Returns:
            The response of the prediction request.
        """
        pass


class PredictionHandler(Handler):
    """Default prediction handler for the prediction requests sent to the application."""

    def __init__(
        self, gcs_artifacts_uri: str, predictor: Optional[Type[Predictor]] = None,
    ):
        """Initializes a Handler instance.

        Args:
            gcs_artifacts_uri (str):
                Required. The value of the environment variable AIP_STORAGE_URI.
            predictor (Type[Predictor]):
                Optional. The Predictor class this handler uses to initiate predictor
                instance if given.
        """
        if predictor is None:
            raise ValueError(
                "PredictionHandler must have a predictor class passed to the init function."
            )

        self._predictor = predictor()
        self._predictor.load(gcs_artifacts_uri)

    async def handle(self, request: Request) -> Response:
        """Handles a prediction request.

        Args:
            request (Request):
                Required. The prediction request sent to the application.

        Returns:
            The response of the prediction request.
        """
        request_body = await request.body()
        content_type = handler_utils.get_content_type_from_headers(request.headers)
        prediction_input = DefaultSerializer.deserialize(request_body, content_type)

        prediction_results = self._predictor.postprocess(
            self._predictor.predict(self._predictor.preprocess(prediction_input))
        )

        accept = handler_utils.get_content_type_from_headers(request.headers)
        data = DefaultSerializer.serialize(prediction_results, accept)
        return Response(content=data, media_type=accept)
