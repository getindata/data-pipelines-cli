import unittest

from data_pipelines_cli.docker_response_reader import DockerResponseReader
from data_pipelines_cli.errors import DockerErrorResponseError


class DockerResponseReaderTestCase(unittest.TestCase):
    def test_status(self):
        docker_response = [
            '{"status":"The push refers to repository [docker.io/library/rep]"}',
            '{"status":"abcdef"}',
        ]
        reader = DockerResponseReader(docker_response)
        self.assertListEqual(
            ["The push refers to repository [docker.io/library/rep]", "abcdef"],
            list(map(str, reader.read_response())),
        )

    def test_stream(self):
        docker_response = [
            '{"stream":"Step 1/10 : FROM abc/blabla:tag123\\n\\n\\n'
            " ---> abcdef123456\\n\\n"
            'Step 2/10 : ADD some_important_dir /var/importantes/\\n\\n"}',
        ]
        reader = DockerResponseReader(docker_response)
        self.assertListEqual(
            [
                "Step 1/10 : FROM abc/blabla:tag123",
                " ---> abcdef123456",
                "Step 2/10 : ADD some_important_dir /var/importantes/",
            ],
            list(map(str, reader.read_response())),
        )

    def test_aux(self):
        docker_response = [
            '{"aux":'
            "{"
            '"Digest": "abcde", '
            '"ID": "sha256:99bb86b06ec9a43d0be231c8794666c1dba8ac38a9d6f46656fd286137db092d"'  # noqa: E501
            "}"
            "}",
        ]
        reader = DockerResponseReader(docker_response)
        self.assertListEqual(
            [
                "Digest: abcde",
                "ID: sha256:99bb86b06ec9a43d0be231c8794666c1dba8ac38a9d6f46656fd286137db092d",  # noqa: E501
            ],
            list(map(str, reader.read_response())),
        )

    def test_error(self):
        docker_response = [
            '{"error":"Something went wrong"}',
        ]
        reader = DockerResponseReader(docker_response)
        self.assertListEqual(
            ["ERROR: Something went wrong"], list(map(str, reader.read_response()))
        )

    def test_error_detail(self):
        docker_response = [
            '{"errorDetail":{"message": "Something went wrong"}}',
            '{"errorDetail":{"message": "Something went really wrong", "code": 500}}',
        ]
        reader = DockerResponseReader(docker_response)
        self.assertListEqual(
            [
                "ERROR: Something went wrong",
                "ERROR: Something went really wrong\nError code: 500",
            ],
            list(map(str, reader.read_response())),
        )

    def test_error_raised(self):
        docker_response = [
            '{"status":"The push refers to repository [docker.io/library/rep]"}',
            '{"status":"abcdef"}',
            '{"errorDetail":{"message": "Something went wrong"}}',
        ]
        with self.assertRaises(DockerErrorResponseError):
            reader = DockerResponseReader(docker_response)
            reader.click_echo_ok_responses()
