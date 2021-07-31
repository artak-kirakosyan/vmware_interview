import copy
import ipaddress as ip
import logging
import os
import re
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from pprint import pprint
from typing import List, Dict, Iterable

import paramiko


class Command:
    def __init__(self, command_name: str, command: str):
        self.command_name = command_name
        self.command = command

    def __repr__(self):
        return "Command(%s, %s)" % (self.command_name, self.command)


class HostCredentials:
    """
    Basic class to represent single host's credentials
    """
    __ip_address_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    __username_pattern = r"(\w+)"
    __password_pattern = r"(\w+)"
    __ip_separator = ", "
    __username_separator = "/"
    __pattern = "%s%s%s%s%s" % (
        __ip_address_pattern, __ip_separator, __username_pattern, __username_separator, __password_pattern
    )
    __compiled_pattern = re.compile(__pattern)

    def __init__(
            self,
            ip_address: str,
            username: str,
            password: str = None,
            private_key_file: str = None,
    ):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.private_key_file = private_key_file

        if private_key_file is not None:
            self.private_key = paramiko.RSAKey.from_private_key_file(private_key_file)
        else:
            self.private_key = None

    def __repr__(self):
        return "HostCredentials('%s', '%s', '%s', %s)" % (
            self.ip_address, self.username, self.password, self.private_key_file
        )

    @classmethod
    def get_host_credentials_from_line(
            cls,
            line: str,
    ) -> "HostCredentials":
        """
        Try to match a ip_address, username and password from the given line.
        Return HostnameCredentials object if succeed, otherwise raise ValueError
        :param line: a single line from the given configuration file
        :return:
        """
        match = re.match(cls.__compiled_pattern, line)
        if match is None:
            raise ValueError("Failed to match host credentials")

        groups = match.groups()
        try:
            ip_address, username, password = groups
        except ValueError as e:
            raise ValueError("Some of the credentials didn't match: %s " % e)
        try:
            ip.ip_address(ip_address)
        except Exception as e:
            msg = "Invalid ip address '%s': error: '%s'" % (ip_address, e)
            logging.warning(msg)
            raise ValueError(msg)
        return cls(
            ip_address=ip_address, username=username, password=password
        )


class SSHExecutor:
    __default_commands_list = [
        Command("Storage", "df -h /"),
    ]

    def __init__(
            self,
            host: HostCredentials,
            timeout: int = 5,
            commands_list: List[Command] = None,
    ):
        """
        Initialize the ssh connection client
        :param timeout: connection timeout
        :param commands_list: list of commands
        """
        if commands_list is None:
            commands_list = copy.deepcopy(self.__default_commands_list)
        self.commands = commands_list

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.load_system_host_keys()
        self.timeout = timeout
        self.host = host

    def connect(self):
        logging.debug("Connecting to %s" % self.host)
        try:
            self.client.connect(
                hostname=self.host.ip_address,
                username=self.host.username,
                password=self.host.password,
                pkey=self.host.private_key,
                timeout=self.timeout,
            )
        except paramiko.ssh_exception.AuthenticationException as e:
            msg = "Failed to connect to %s: %s" % (self.host.ip_address, e)
            logging.error(msg)
            raise e

    def execute_commands(self) -> Dict[str, Dict[str, str]]:
        results = {}
        for command in self.commands:
            results[command.command_name] = self.execute_command(command)
        return results

    def execute_command(self, command: Command) -> Dict[str, str]:
        try:
            _, std_out, std_err = self.client.exec_command(command=command.command)
        except paramiko.SSHException as e:
            logging.error("Failed on %s" % command)
            output = None
            error = "Failed to execute %s: %s" % (command, e)
        else:
            output = std_out.read().decode()
            error = std_err.read().decode()
        return {
            "output": output,
            "error": error,
        }

    def get_commands_results(self) -> Dict:
        try:
            self.connect()
        except paramiko.AuthenticationException as e:
            status = "Authentication error"
            result = {}
            logging.error("Authentication error when connecting to %s: %s" % (self.host, e))
        except socket.timeout as e:
            status = "Connection timout"
            result = {}
            logging.error("Connection timed out on %s: %s" % (self.host, e))
        else:
            status = "Success"
            logging.debug("Connected to %s, executing commands" % (self.host,))
            result = self.execute_commands()
        finally:
            self.client.close()
        results = {"status": status, "result": result}
        return results


def get_hosts(file_path: str):
    if not os.path.isfile(file_path):
        raise ValueError("%s file does not exist" % file_path)
    with open(file_path, "r") as f:
        for line in f:
            yield line


def get_active_hosts(file_path: str, comment_symbol: str = ";"):
    for line in get_hosts(file_path):
        if line.startswith(comment_symbol):
            logging.warning("Commented line:\n\t'%s'" % line)
            continue
        else:
            yield line


def get_host_credentials(file_path: str, comment_symbol: str = ";") -> Iterable[HostCredentials]:
    for line in get_active_hosts(file_path, comment_symbol):
        try:
            host = HostCredentials.get_host_credentials_from_line(line)
        except ValueError:
            logging.error("Failed to get host info from %s" % line)
            continue
        else:
            yield host


def connect_and_get_results(host: HostCredentials) -> Dict[HostCredentials, Dict]:
    client = SSHExecutor(host=host)
    res = client.get_commands_results()
    pprint(res)
    return {host: res}


def check_all_hosts_status(file_path, pool_size=10) -> List[Dict]:
    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        results = executor.map(connect_and_get_results, get_host_credentials(file_path=file_path, comment_symbol=";"))
    return list(results)


def main():
    try:
        file_path = sys.argv[1]
    except IndexError:
        print("Pass file name or path as an argument")
        sys.exit(1)
    results = check_all_hosts_status(file_path=file_path)
    pprint(results)


if __name__ == "__main__":
    main()
