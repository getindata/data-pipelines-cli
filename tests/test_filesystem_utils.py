import pathlib
import random
import string
import unittest

import boto3
import fsspec
from botocore.exceptions import ClientError
from moto.server import ThreadedMotoServer

from data_pipelines_cli.errors import DataPipelinesError

MY_BUCKET = "my_bucket"


class TestError(unittest.TestCase):
    def test_wrong_local_path(self):
        from data_pipelines_cli.filesystem_utils import LocalRemoteSync

        wrong_local_path = pathlib.Path(__file__).parent.joinpath(
            "".join(random.choices(string.ascii_letters + string.digits, k=25))
        )
        remote_path = "".join(random.choices(string.ascii_letters + string.digits + "/", k=25))
        with self.assertRaises(DataPipelinesError):
            LocalRemoteSync(wrong_local_path, remote_path, {}).sync(delete=False)


class TestSynchronize(unittest.TestCase):
    test_sync_2nd_directory_layout = [
        "test2.txt",
        str(pathlib.Path("a").joinpath("b", "c", "xyz")),
    ]
    test_sync_directory_layout = ["test1.txt", *test_sync_2nd_directory_layout]

    def _test_synchronize(self, protocol: str, **remote_kwargs):
        from data_pipelines_cli.filesystem_utils import LocalRemoteSync

        local_path = pathlib.Path(__file__).parent.joinpath("goldens", "test_sync_directory")
        remote_path = f"{protocol}://{MY_BUCKET}/"
        LocalRemoteSync(local_path, remote_path, remote_kwargs).sync(delete=False)

        remote_fs, _ = fsspec.core.url_to_fs(remote_path, **remote_kwargs)
        for local_file in self.test_sync_directory_layout:
            self.assertIn(
                str(pathlib.Path(MY_BUCKET).joinpath(local_file)),
                remote_fs.find(MY_BUCKET),
            )

    def _test_synchronize_with_delete(self, protocol: str, **remote_kwargs):
        from data_pipelines_cli.filesystem_utils import LocalRemoteSync

        local_path = pathlib.Path(__file__).parent.joinpath("goldens", "test_sync_directory")
        remote_path = f"{protocol}://{MY_BUCKET}/"
        LocalRemoteSync(local_path, remote_path, remote_kwargs).sync(delete=True)

        remote_fs, _ = fsspec.core.url_to_fs(remote_path, **remote_kwargs)
        for local_file in self.test_sync_directory_layout:
            self.assertIn(
                str(pathlib.Path(MY_BUCKET).joinpath(local_file)),
                remote_fs.find(MY_BUCKET),
            )

        local_path_2 = pathlib.Path(__file__).parent.joinpath("goldens", "test_sync_2nd_directory")
        LocalRemoteSync(
            local_path_2,
            remote_path,
            remote_kwargs,
        ).sync(delete=True)
        for local_file in self.test_sync_2nd_directory_layout:
            self.assertIn(
                str(pathlib.Path(MY_BUCKET).joinpath(local_file)),
                remote_fs.find(MY_BUCKET),
            )
        self.assertNotIn(
            str(pathlib.Path(MY_BUCKET).joinpath("test1.txt")),
            remote_fs.find(MY_BUCKET),
        )


class TestS3Synchronize(TestSynchronize):
    """
    S3 tests using moto server mode for aiobotocore compatibility.
    The @mock_s3 decorator doesn't work with aiobotocore's async operations.
    """

    @classmethod
    def setUpClass(cls):
        # Start moto server on localhost for aiobotocore compatibility
        cls.server = ThreadedMotoServer(port="5555", verbose=False)
        cls.server.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()

    def setUp(self) -> None:
        # Create S3 client pointing to moto server
        self.endpoint_url = "http://127.0.0.1:5555"
        client = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            endpoint_url=self.endpoint_url,
        )

        # Create bucket
        try:
            client.create_bucket(Bucket=MY_BUCKET)
        except client.exceptions.BucketAlreadyExists:
            pass

    def tearDown(self):
        # Clean up bucket contents
        client = boto3.client(
            "s3",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
            endpoint_url=self.endpoint_url,
        )
        try:
            # Delete all objects
            response = client.list_objects_v2(Bucket=MY_BUCKET)
            if "Contents" in response:
                for obj in response["Contents"]:
                    client.delete_object(Bucket=MY_BUCKET, Key=obj["Key"])
            # Delete bucket
            client.delete_bucket(Bucket=MY_BUCKET)
        except ClientError:
            pass

    def test_synchronize(self):
        self._test_synchronize(
            "s3",
            key="testing",
            secret="testing",
            client_kwargs={"endpoint_url": self.endpoint_url},
        )

    def test_synchronize_with_delete(self):
        self._test_synchronize_with_delete(
            "s3",
            key="testing",
            secret="testing",
            client_kwargs={"endpoint_url": self.endpoint_url},
        )


class TestGoogleStorageSynchronize(TestSynchronize):
    def setUp(self) -> None:
        from gcp_storage_emulator.server import create_server

        self.server = create_server("localhost", 9023, in_memory=True, default_bucket=MY_BUCKET)
        self.server.start()

    def tearDown(self):
        self.server.stop()

    def test_synchronize(self):
        self._test_synchronize("gs", endpoint_url="http://localhost:9023", token="anon")

    def test_synchronize_with_delete(self):
        self._test_synchronize_with_delete("gs", endpoint_url="http://localhost:9023", token="anon")
