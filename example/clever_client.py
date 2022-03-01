"""
Example of Clever Cloud Python Client to deploy and manage applications.
Used to understand the Clever Cloud add-on api
"""
import json
import logging
import os
import subprocess
from typing import List, Dict, Union


class CleverToolsMissingClient(Exception):
    pass


class CleverToolsMissingSecrets(Exception):
    pass


def is_normalize_strings_equal(str1: str, str2: str) -> bool:
    return ' '.join(str1.split()).lower() == ' '.join(str2.split()).lower()


class CleverCloud(object):
    def __init__(self, force: bool = False):
        # check if clever tools are installed
        ret_process = subprocess.run(["whereis", "clever"], capture_output=True)
        ret_process = ret_process.stdout.decode("utf-8")

        if "clever" not in ' '.join(ret_process.split(":")[1:]):
            if not force:
                raise CleverToolsMissingClient("clever client not found !")

    # CLEVER_SECRET must be provided as env variable.
    # Get the secret with
    # `https://www.clever-cloud.com/doc/reference/clever-tools/getting_started/#linking-your-account`
        if not 'CLEVER_SECRET' in os.environ and not 'CLEVER_SECRET' in os.environ:
            if not force:
                raise CleverToolsMissingSecrets()

    @staticmethod
    def _create_app(app_name: str, organisation: str, app_type: str = 'python') -> bool:
        logging.debug("CLI: create app")
        ret_process = subprocess.run(['clever', 'create', app_name,
                                      '--type', app_type, '--org', organisation],
                                     capture_output=True).stdout.decode('utf-8')

        if not is_normalize_strings_equal(ret_process,
                                          'Your application has been successfully created!'):
            logging.error("Error during app creation\n %s" % ret_process)
            return False
        return True

    @staticmethod
    def _get_applications_list() -> List[Dict]:
        logging.debug('CLI: get apps list')
        # No .clever.json file
        if not os.path.exists('.clever.json'):
            return []
        with open('.clever.json', 'r') as fd:
            ret = json.load(fd)

        if 'apps' not in ret.keys():
            return []
        return ret['apps']

    @staticmethod
    def _unlink_app(app_name: str) -> bool:
        logging.debug('CLI : unlink app')
        ret_process = subprocess.run(["clever", 'unlink', app_name],
                                     capture_output=True).stdout.decode('utf-8')

        if not is_normalize_strings_equal(ret_process,
                                          "Your application has been successfully unlinked!"):
            logging.error("Error to unlink application:\n%s" % ret_process)
            return False

        return True

    @staticmethod
    def _remove_clever_file():
        if os.path.exists(".clever.json"):
            os.remove(".clever.json")

    def create_application(self, app_name: str, organisation: str, app_type: str = 'python') -> \
            Union[Dict, None]:
        if not self._create_app(app_name, organisation, app_type):
            return

        app_info = [x for x in self._get_applications_list() if x["name"] == app_name]
        if len(app_info) == 0:
            logging.error("There is no linked application")
            return
        elif len(app_info) > 1:
            logging.error("There is too many linked application :\n %s" % json.dumps(app_info))
            if os.path.exists(".clever.json"):
                self._remove_clever_file()
                return self.create_application(app_name=app_name, organisation=organisation,
                                               app_type=app_type)
            return

        if not self._unlink_app(app_name):
            return

        return app_info[0]

    def _link_app(self, app_id: str) -> bool:
        logging.debug('CLI : link app')
        ret_process = subprocess.run(["clever", 'link', app_id],
                                     capture_output=True)
        ret_process_err = ret_process.stderr.decode('utf-8')
        ret_process = ret_process.stdout.decode('utf-8')
        if not is_normalize_strings_equal(ret_process,
                                          "Your application has been successfully linked!"):
            logging.error("Unable to link to the application !")
            logging.error("error message %s" % ret_process_err)
            logging.error("Stdout message %s" % ret_process)
            if os.path.exists(".clever.json"):
                logging.error("Try to delete .clever.json file and retry")
                self._remove_clever_file()
                return self._link_app(app_id=app_id)
            return False

        return True

    @staticmethod
    def _delete_app() -> bool:
        logging.debug('CLI: call for deletion')
        ret_process = subprocess.run(["clever", 'delete', '-y'],
                                     capture_output=True)
        ret_process_err = ret_process.stderr.decode('utf-8')
        ret_process = ret_process.stdout.decode('utf-8')
        if not is_normalize_strings_equal(ret_process,
                                          "The application has been deleted"):
            logging.error(
                "Unable to delete the application !\n return value : %s" % ret_process_err)
            return False
        return True

    def delete_application(self, app_id) -> bool:
        self._remove_clever_file()
        if not self._link_app(app_id):
            return False
        if not self._delete_app():
            return False
        return True
