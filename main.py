#!/usr/bin/python3

import os
import sys
import json
from shutil import which

configuration_file = "applications.json"

def print_info(message):
    """
    print information message
    :param message: message to print
    :return: None
    """
    print("[+] " + message)

def print_error(message):
    """
    print error message
    :param message: message to print
    :return: None
    """
    print("[-] " + message)

def print_warning(message):
    """
    print warning message
    :param message: message to print
    :return: None
    """
    print("[!] " + message)

# check if configuration file is provided
if len(sys.argv) == 2:
    print_info("New configuration file provided {}".format(sys.argv[1]))
    configuration_file = sys.argv[1]

# check if configuration file exists
if not os.path.isfile(configuration_file):
    print_error("Configuration file not found")
    sys.exit(1)

# check if git is installed
if not which("git"):
    print_error("git commandline is required to be installed! please install git and re-run the application.")
    sys.exit(1)

# check iof docker is installed
if not which("docker"):
    print_error("docker commandline is required to be installed! please install docker and re-run the application.")
    sys.exit(1)

# check if docker is running without showing output
if os.system("docker ps > /dev/null 2>&1"):
    print_error("docker is not running! please start docker and re-run the application.")
    sys.exit(1)

# check if repositories directory exist
if not os.path.isdir("repositories"):
    os.mkdir("repositories")

configurations = json.load(open(configuration_file))

# get address and directory and clone the repo
def clone_repo(address, directory):
    """
    clone git repository
    :param address: git repository address
    :param directory: directory to clone repository
    :return: None
    """
    os.chdir(directory)
    if not os.path.isdir(address.split("/")[-1]):
        os.system("git clone " + address)
        os.chdir("../../..")
    else:
        os.chdir(address.split("/")[-1])
        os.system("git pull")
        os.chdir("../../../..")


def update_git_repositories(vulnerable, language ,address):
    """
    update or clone git repositories
    :param vulnerable: True if repository is vulnerable, False if repository is non-vulnerable
    :param language: programming language of the repository
    :param address: git repository address
    :return: None
    """
    # clone repositories in repositories directory
    if vulnerable:
        # clone vulnerable repositories into repositories/vulnerable directory
        if not os.path.isdir("repositories/vulnerable"):
            os.mkdir("repositories/vulnerable")
        if not os.path.isdir("repositories/vulnerable/" + language):
            os.mkdir("repositories/vulnerable/" + language)
        directory = "repositories/vulnerable/" + language
        clone_repo(address, directory)
    else:
        # clone non-vulnerable repositories into repositories/non-vulnerable directory
        if not os.path.isdir("repositories/non-vulnerable"):
            os.mkdir("repositories/non-vulnerable")
        if not os.path.isdir("repositories/non-vulnerable/" + language):
            os.mkdir("repositories/non-vulnerable/" + language)
        directory = "repositories/non-vulnerable/" + language
        clone_repo(address, directory)

print_info("Updating git repositories")

# update vulnerable repositories
for language in configurations["vulnerable"]:
    print_info("Updating vulnerable repositories for language {}".format(language))
    for repository in configurations["vulnerable"][language]:
        print_info("Updating vulnerable repository: {}".format( repository))
        update_git_repositories(True, language, repository)

# update non-vulnerable repositories
for language in configurations["non-vulnerable"]:
    print_info("Updating non-vulnerable repositories for language {}".format(language))
    for repository in configurations["non-vulnerable"][language]:
        print_info("Updating non-vulnerable repository: {}".format(repository))
        update_git_repositories(False, language, repository)
       
print_info("Git repositories updated successfully")
