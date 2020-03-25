from collections import Iterable
import logging
import os
import subprocess
import sys
import site
import json

__all__ = ("Mapper",)


class Mapper:
    """
    This class maps all packages from requirements.txt file with its top level modules.

    TODO add ability to get requirements from str, json(as list of requirements), or base64.
    """

    def __init__(self, reqs="requirements.txt", fmt="json", debug=False) -> None:
        self._regs = reqs
        self._fmt = fmt
        self.log = logging.getLogger("pipmap")
        if debug:
            logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        self._site_pkgs = site.getsitepackages()[0]
        if isinstance(self._site_pkgs, list):
            self._site_pkgs = self._site_pkgs[0]
        self._verbose = 'v'
        self._pkgs_map = {}

    def _cmd(self, cmd: list) -> tuple:
        """
        Method to execute command and capture the stdout as a result

        :param cmd: list of cmd and args. Example: ["pip", "show", "requests"]
        :return: tuple(stdout, stderr)
        """
        self.log.debug(f"Start to execute cmd: {cmd}")
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode()
        self.log.debug(f"cmd: {cmd}. stdout: {stdout}")
        stderr = result.stderr.decode()
        if stderr:
            self.log.debug(f"cmd: {cmd}. stderr: {stderr}")
        return stdout, stderr

    def _split(self, data: Iterable, delimiter: str = "==") -> any:
        """
        Split list of lines by delimiter.

        :param data: list of lines
        :param delimiter: str to split line
        :raise Exception: If data is not iterable will raise Exception
        :return: dict
        """
        if not hasattr(data, '__iter__'):
            self.log.error(f"Data are not iterable instance: {data}")
            raise Exception(f"Data are not iterable instance: {data}")
        reqs = [r.strip().split(delimiter, 1) for r in data if r.find(delimiter) > -1]
        return {key.strip(): value.strip() for (key, value) in reqs}

    def _get_pkg_path(self, name: str, version: str) -> any:
        """
        This method finds the package info location.
        Try to looking for in the site-packages location and with suffixes [.egg-info, .dist-info] directories
        If any path not exists raise an Exception

        :param name: package name
        :param version: package version
        :raise Exception if the package location not found
        :return: path of the package location
        """
        print(f"name: ${name}")
        print(f"version: ${version}")
        pkg_path_tmpl = "{name}-{version}.{suffix}-info"
        suffixes = ["egg", "dist"]
        for suf in suffixes:
            _pkg_location = pkg_path_tmpl.format(name=name, version=version, suffix=suf)
            _pkg_path = os.path.join(self._site_pkgs, _pkg_location)
            _pkg_location2 = pkg_path_tmpl.format(name=name.replace("-", "_"), version=version, suffix=suf)
            _pkg_path2 = os.path.join(self._site_pkgs, _pkg_location2)
            self.log.debug(f"pkg:{name}:{version} check location {_pkg_path}")
            if os.path.exists(_pkg_path):
                return _pkg_path
            elif os.path.exists(_pkg_path2):
                return _pkg_path2

        else:
            self.log.error(f"Package dir not found for {name}:{version}")

        return None

    def _read(self, path: str) -> any:
        """
        Read file from path and returns striped lines

        :param path: str
        """
        # TODO validate path
        self.log.debug(f"Start to read file: {path}")
        if not os.path.exists(path):
            self.log.error(f"File not found in the path: {path}")
            raise Exception(f"File not found in the path: {path}")
        with open(path, 'r') as fin:
            lines = fin.readlines()
            self.log.debug(f"Finished reading the file: {lines}")
        return lines

    def _install(self, name: str, version: str) -> tuple:
        """
        Install package from requirements file with pip

        :param name: str
        :param version: str
        :return: tuple
        """
        res, err = self._cmd(["pip", "install", f"{name}=={version}"])
        if err:
            # TODO handle err
            # todo add to mapping as not installed
            self.log.error(f"Package {name}:{version} not installed: {err}")
        return res, err

    def _get_pkg_meta(self, location: str) -> any:
        """
        Read package metadata from package location

        :param location:
        :return: dict
        """
        self.log.debug(f"Get meta from location: {location}")
        _meta_file = "METADATA"
        if location.endswith("egg-info"):
            _meta_file = "PKG-INFO"
        if not os.path.exists(os.path.join(location, _meta_file)):
            self.log.warning(f"{_meta_file} not found in the {location}")
            return None
        _file_data = self._read(os.path.join(location, _meta_file))
        _meta_data = self._split(_file_data, ":")
        return _meta_data

    def _get_pkg_top_level(self, location: str) -> any:
        """
        Read package top_level file from package location and return list of the package's top modules

        :param location:
        :return:
        """
        self.log.debug("Get top level from location: {location}")
        _toplevel_file = "top_level.txt"
        if not os.path.exists(os.path.join(location, _toplevel_file)):
            self.log.warning(f"{_toplevel_file} not found in the {location}")
            return None
        _file_data = self._read(os.path.join(location, _toplevel_file))
        _modules = [m.strip() for m in _file_data]
        return _modules

    def _add_pkg_data(self, name: str, version: str) -> any:
        """
        Update installed package with detail information

        :param name:
        :param version:
        :return:
        """
        _pkg_location = self._get_pkg_path(name, version)
        if _pkg_location is None:
            return
        self.log.debug(f"pkg{name}:{version} | location: {_pkg_location}")
        _pkg_meta = self._get_pkg_meta(_pkg_location)
        self.log.debug(f"pkg{name}:{version} | meta: {_pkg_meta}")
        _pkg_name = _pkg_meta.get("Name") or name
        _pkg_modules = self._get_pkg_top_level(_pkg_location)
        self.log.debug(f"pkg{name}:{version} | _pkg_modules: {_pkg_modules}")

        # collect package by metadata name
        # collect raw str from requirements as the name can be different
        self._pkgs_map[_pkg_name] = {
            # all details
            "metadata": _pkg_meta,
            "requirements": {
                "name": name,
                "version": version,
                "raw": f"{name}=={version}"
            },
            "top_level": _pkg_modules
        }

    def _format(self) -> any:
        """
        :Example of package info
        {
          "refinitiv-dataplatform": {
            "metadata": {
              "Metadata-Version": "2.1",
              "Name": "refinitiv-dataplatform",
              "Version": "1.0.0a0",
              "Summary": "Python package for retrieving data.",
              "Home-page": "https://developers.refinitiv.com/refinitiv-data-platform/refinitiv-data-platform-libraries",
              "Author": "REFINITIV",
              "Author-email": "UNKNOWN",
              "License": "LICENSE",
              "Requires-Dist": "deprecation"
            },
            "requirements": {
              "name": "refinitiv_dataplatform",
              "version": "1.0.0a0",
              "raw": "refinitiv_dataplatform==1.0.0a0"
            },
            "top_level": [
              "refinitiv"
            ]
          }
        }

        :return:
        """
        # todo add package detail level as --verbose[v, vv]
        pkgs_info = []
        if self._verbose == 'v':
            for pkg, data in self._pkgs_map.items():
                _reqs_name = data.get("requirements", {}).get("name")
                _pkg = {
                    "name": pkg,
                    "version": data.get("metadata", {}).get("Version", "UNKNOWN"),
                    "modules": data.get("top_level", []),
                    "alias": _reqs_name if _reqs_name != pkg else ""
                }
                pkgs_info.append(_pkg)

        if self._fmt == "json":
            response = json.dumps(pkgs_info)
        else:
            response = pkgs_info
        return response

    def map(self) -> any:
        """
        TODO How to handle different requiremenents package name and installed package name
        Example:
            requiements.txt
                refinitiv_dataplatform==1.0.0a0
            site-packages:
                refinitiv-dataplatform
        :return:
        """
        self._cmd(["pip", "install", "--upgrade", "pip"])
        reqs_lines = self._read(self._regs)
        reqs_dict = self._split(reqs_lines)
        for name, version in reqs_dict.items():
            _, err = self._install(name, version)
            if err:
                self.log.error(f"Problem to install {name}:{version}. Error: {err}")
                # todo handle error
                continue
            self._add_pkg_data(name, version)
        return self._format()
