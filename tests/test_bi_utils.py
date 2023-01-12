import unittest
from unittest.mock import MagicMock, patch

from data_pipelines_cli.bi_utils import BiAction, _bi_looker, bi
from data_pipelines_cli.errors import DataPipelinesError, NotSuppertedBIError


class BiUtilsTestCase(unittest.TestCase):
    def test_bi_compile_looker(self):
        bi_config = {
            "is_bi_enabled": True,
            "bi_target": "looker",
            "is_bi_compile": True,
            "is_bi_deploy": False,
        }

        _bi_looker_mock = MagicMock()

        with patch("data_pipelines_cli.bi_utils.read_bi_config", return_value=bi_config), patch(
            "data_pipelines_cli.bi_utils._bi_looker", _bi_looker_mock
        ):
            bi("env", BiAction.COMPILE)
            _bi_looker_mock.assert_called_with("env", True, False, None)

    def test_bi_deploy_looker(self):
        bi_config = {
            "is_bi_enabled": True,
            "bi_target": "looker",
            "is_bi_compile": True,
            "is_bi_deploy": True,
        }

        _bi_looker_mock = MagicMock()

        with patch("data_pipelines_cli.bi_utils.read_bi_config", return_value=bi_config), patch(
            "data_pipelines_cli.bi_utils._bi_looker", _bi_looker_mock
        ):
            bi("env", BiAction.DEPLOY)
            _bi_looker_mock.assert_called_with("env", False, True, None)

    def test_bi_disabled(self):
        bi_config = {
            "is_bi_enabled": False,
            "bi_target": "looker",
            "is_bi_compile": True,
            "is_bi_deploy": False,
        }

        _bi_looker_mock = MagicMock()

        with patch("data_pipelines_cli.bi_utils.read_bi_config", return_value=bi_config), patch(
            "data_pipelines_cli.bi_utils._bi_looker", _bi_looker_mock
        ):
            bi("env", BiAction.COMPILE)
            _bi_looker_mock.assert_not_called()

    @patch("data_pipelines_cli.bi_utils._bi_looker")
    @patch("data_pipelines_cli.bi_utils.read_bi_config")
    def test_bi_disabled_when_config_not_exists(self, mock_read_bi_config, mock__bi_looker):
        mock_read_bi_config.return_value = {}
        bi("non_existent_env", BiAction.COMPILE)
        mock__bi_looker.assert_not_called()

    def test_bi_not_supported_bi(self):
        bi_config = {
            "is_bi_enabled": True,
            "bi_target": "superset",
            "is_bi_compile": True,
            "is_bi_deploy": False,
        }

        with patch("data_pipelines_cli.bi_utils.read_bi_config", return_value=bi_config):
            self.assertRaises(NotSuppertedBIError, bi, "env", BiAction.COMPILE)

    def test_bi_looker_compile(self):
        generate_lookML_model_mock = MagicMock()
        deploy_lookML_model_mock = MagicMock()
        with patch(
            "data_pipelines_cli.bi_utils.generate_lookML_model", generate_lookML_model_mock
        ), patch("data_pipelines_cli.bi_utils.deploy_lookML_model", deploy_lookML_model_mock):
            _bi_looker("env", True)

        generate_lookML_model_mock.assert_called_once()
        deploy_lookML_model_mock.assert_not_called()

    def test_bi_looker_deploy(self):
        generate_lookML_model_mock = MagicMock()
        deploy_lookML_model_mock = MagicMock()
        with patch(
            "data_pipelines_cli.bi_utils.generate_lookML_model", generate_lookML_model_mock
        ), patch("data_pipelines_cli.bi_utils.deploy_lookML_model", deploy_lookML_model_mock):
            _bi_looker("env", False, True, "/path/to/git/key")

        generate_lookML_model_mock.assert_not_called()
        deploy_lookML_model_mock.assert_called_once()

    def test_bi_looker_deploy_no_key_provided(self):
        generate_lookML_model_mock = MagicMock()
        deploy_lookML_model_mock = MagicMock()
        with patch(
            "data_pipelines_cli.bi_utils.generate_lookML_model", generate_lookML_model_mock
        ), patch("data_pipelines_cli.bi_utils.deploy_lookML_model", deploy_lookML_model_mock):
            self.assertRaises(DataPipelinesError, _bi_looker, "env", False, True)

        generate_lookML_model_mock.assert_not_called()

    def test_bi_not_supported_action(self):
        bi_config = {
            "is_bi_enabled": True,
            "bi_target": "looker",
            "is_bi_compile": True,
            "is_bi_deploy": False,
        }

        _bi_looker_mock = MagicMock()

        with patch("data_pipelines_cli.bi_utils.read_bi_config", return_value=bi_config), patch(
            "data_pipelines_cli.bi_utils._bi_looker", _bi_looker_mock
        ):
            bi("env", 2)
            _bi_looker_mock.assert_called_with("env", False, False, None)
