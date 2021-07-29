import os
import re
import socket
from pprint import pprint
from typing import List, Dict
import copy
import paramiko


def get_hosts(file_path: str):
    if not os.path.isfile(file_path):
        raise ValueError("%s file does not exist" % file_path)
    with open(file_path, "r") as f:
        for line in f:
            yield line


def get_active_hosts(file_path: str, comment_symbol: str = "#"):
    for line in get_hosts(file_path):
        if line.startswith(comment_symbol):
            print("Commented line:\n\t'%s'" % line)
            continue
        else:
            yield line


class Command:
    def __init__(self, command_name: str, command: str):
        self.command_name = command_name
        self.command = command

    def __repr__(self):
        return "Command(%s, %s)" % (self.command_name, self.command)


class HostCredentials:
    def __init__(
            self,
            hostname: str,
            username: str,
            password: str = None,
            private_key_file: str = None,
    ):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.private_key_file = private_key_file

        if private_key_file is not None:
            self.private_key = paramiko.RSAKey.from_private_key_file(private_key_file)
        else:
            self.private_key = None

    def __repr__(self):
        return "HostCredentials(%s, %s, %s, %s)" % (self.hostname, self.username, self.password, self.private_key_file)

    @classmethod
    def get_host_credentials_from_line(
            cls,
            line: str,
            hostname_separator: str = ", ",
            username_password_separator: str = "/",
    ) -> "HostCredentials":
        pattern = re.compile(
            r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})%s(\w+)%s(\w+)" % (hostname_separator, username_password_separator)
        )
        match = re.match(pattern, line)
        if match is None:
            raise ValueError("Failed to match host credentials")

        groups = match.groups()
        try:
            hostname, username, password = groups
        except ValueError as e:
            raise ValueError("Some of the credentials didn't match: %s " % e)

        return cls(
            hostname=hostname, username=username, password=password
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
        self.client.load_system_host_keys()
        self.timeout = timeout
        self.host = host

    def connect(self):
        try:
            self.client.connect(
                hostname=self.host.hostname,
                username=self.host.username,
                password=self.host.password,
                pkey=self.host.private_key,
                timeout=self.timeout,
            )
        except paramiko.ssh_exception.AuthenticationException as e:
            msg = "Failed to connect to %s: %s" % (self.host.hostname, e)
            print(msg)
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
            print("Failed on %s" % command)
            output = None
            error = "Failed to execute %s: %s" % (command, e)
        else:
            output = std_out.read().decode()
            error = std_err.read().decode()
        return {
            "output": output,
            "error": error,
        }

    def get_commands_results(self) -> Dict[str, Dict[str, str]]:
        try:
            self.connect()
            results = self.execute_commands()
        except paramiko.AuthenticationException as e:
            print("Authentication error on connection: %s" % e)
            results = {}
        except socket.timeout as e:
            print("Connection timed out: %s" % e)
            results = {}
        finally:
            self.client.close()
        return results


def main():
    for line in get_active_hosts(file_path="hosts.txt"):
        try:
            host = HostCredentials.get_host_credentials_from_line(line)
        except ValueError:
            print("Failed to get host info from %s" % line)
            continue

        client = SSHExecutor(host=host)
        res = client.get_commands_results()
        pprint(res)


if __name__ == "__main__":
    main()
