import pathlib
import random
import string
import unittest

import boto3
import botocore
import fsspec
import moto
from moto import mock_s3

from data_pipelines_cli.errors import DataPipelinesError

MY_BUCKET = "my_bucket"


# According to
# https://github.com/aio-libs/aiobotocore/issues/755#issuecomment-844273191
# aiobotocore problems can be fixed by creating an AWSResponse with fixed
# `raw_headers` field
class MockedAWSResponse(botocore.awsrequest.AWSResponse):
    raw_headers = {}  # type: ignore

    async def read(self):  # type: ignore
        return self.text


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


@mock_s3
class TestS3Synchronize(TestSynchronize):
    def setUp(self) -> None:
        botocore.awsrequest.AWSResponse = MockedAWSResponse
        moto.core.models.AWSResponse = MockedAWSResponse

        client = boto3.client(
            "s3",
            region_name="eu-west-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        try:
            s3 = boto3.resource(
                "s3",
                region_name="eu-west-1",
                aws_access_key_id="testing",
                aws_secret_access_key="testing",
            )
            s3.meta.client.head_bucket(Bucket=MY_BUCKET)
        except botocore.exceptions.ClientError:
            pass
        else:
            err = "{bucket} should not exist.".format(bucket=MY_BUCKET)
            raise EnvironmentError(err)

        client.create_bucket(
            Bucket=MY_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )

    def tearDown(self):
        s3 = boto3.resource(
            "s3",
            region_name="eu-west-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        bucket = s3.Bucket(MY_BUCKET)
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()

    def test_synchronize(self):
        self._test_synchronize("s3", key="testing", password="testing")

    def test_synchronize_with_delete(self):
        self._test_synchronize_with_delete("s3", key="testing", password="testing")


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
