# Copyright 2026 Google LLC
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


class ClientError(Exception):
    """Base exception for all client errors."""


class NotFoundError(ClientError):
    """Raised when a resource is not found."""

    pass


class AlreadyExistsError(ClientError):
    """Raised when a resource already exists."""

    pass


class IllegalArgumentError(ClientError):
    """Raised when an argument is invalid."""

    pass


class FailedOperationError(ClientError):
    """Raised when an operation failed."""

    pass


class ResourceQuotaExceededError(ClientError):
    """Raised when a resource quota limit is exceeded."""

    pass


class FailedPreconditionError(ClientError):
    """Raised when the request or resource is not in the correct state."""

    pass
