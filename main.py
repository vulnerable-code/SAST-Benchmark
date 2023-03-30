#!/usr/bin/python3

import os
import sys
import json
import multiprocessing
import glob
import time
import json
from shutil import which

max_workers = 5
processes = []
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

def multiprocess_worker(function, args):
    """
    worker function for multiprocessing
    :param vulnerable: True if repository is vulnerable, False if repository is non-vulnerable
    :param language: programming language of the repository
    :param address: git repository address
    :return: None
    """
    while True:
        if len(multiprocessing.active_children()) < max_workers + 1:
            break
        time.sleep(0.1)
    process = multiprocessing.Process(target=function, args=args)
    process.start()
    processes.append(process)

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
            os.system("mkdir -p repositories/vulnerable")
        if not os.path.isdir("repositories/vulnerable/" + language):
            os.system("mkdir -p repositories/vulnerable/" + language)
        directory = "repositories/vulnerable/" + language
    else:
        # clone non-vulnerable repositories into repositories/non-vulnerable directory
        if not os.path.isdir("repositories/non-vulnerable"):
            os.system("mkdir -p repositories/non-vulnerable")
        if not os.path.isdir("repositories/non-vulnerable/" + language):
            os.system("mkdir -p repositories/non-vulnerable/" + language)
        directory = "repositories/non-vulnerable/" + language
    clone_repo(address, directory)

# docker run --rm -e "WORKSPACE=${PWD}" -v $PWD:/app shiftleft/scan scan --local-only
def run_shiftleft_scan(vulnerable, language, address):
    """
    run shiftleft scan on repository
    :param vulnerable: True if repository is vulnerable, False if repository is non-vulnerable
    :param language: programming language of the repository
    :param address: git repository address
    :return: None
    """
    current_directory = os.getcwd()
    # run shiftleft scan on repositories
    if vulnerable:
        # run shiftleft scan on vulnerable repositories
        directory = "repositories/vulnerable/" + language + "/" + address.split("/")[-1]
        project_directory = current_directory + "/" + directory
    else:
        # run shiftleft scan on non-vulnerable repositories
        directory = "repositories/non-vulnerable/" + language + "/" + address.split("/")[-1]
        project_directory = current_directory + "/" + directory
    os.system(f"docker run --rm -e \"WORKSPACE={project_directory}\" -v {project_directory}:/app shiftleft/scan scan --local-only")


def create_codeql_databases(language):
    """
    create codeql databases
    :param language: programming language of the repository
    :return: None
    """
    os.system('''docker run --rm --name codeql-docker -v "/tmp/src:/opt/src" -v "/tmp/results:/opt/results" -e "LANGUAGE=go" j3ssie/codeql-docker:latest''')

def run_codeql_scan(vulnerable, language, codeql_language, address):
    """
    run codeql scan on repository
    :param vulnerable: True if repository is vulnerable, False if repository is non-vulnerable
    :param language: programming language of the repository
    :param codeql_language: codeql language of the repository
    :param address: git repository address
    :return: None
    """
    # docker run --rm --name codeql-container -it -v /home/azureuser/SAST-Benchmark/codeql-dbs/python:/database -v /home/azureuser/SAST-Benchmark/repositories/vulnerable/Python/pygoat:/src --entrypoint /bin/bash mcr.microsoft.com/cstsectools/codeql-container -c "codeql database create --language=python --threads=0 --source-root /src /database --overwrite && cd /src && codeql database analyze /database --threads=0 --format csv -o /src/codeql-results.csv" 
    current_directory = os.getcwd()
    # run codeql scan on repositories
    if vulnerable:
        # run codeql scan on vulnerable repositories
        directory = "repositories/vulnerable/" + language + "/" + address.split("/")[-1]
        project_directory = current_directory + "/" + directory
    else:
        # run codeql scan on non-vulnerable repositories
        directory = "repositories/non-vulnerable/" + language + "/" + address.split("/")[-1]
        project_directory = current_directory + "/" + directory
    os.system(f"docker run --rm --name codeql-container -it -v {project_directory}:/src --entrypoint /bin/bash mcr.microsoft.com/cstsectools/codeql-container -c \"codeql database create --language={codeql_language} --threads=0 --source-root /src /src/database --overwrite && cd /src && codeql database analyze /src/database --threads=0 --format csv -o /src/codeql-results.csv\"")
    

print_info("Updating git repositories")
if __name__ == '__main__':
    # update vulnerable repositories
    # for language in configurations["vulnerable"]:
    #     print_info("Updating vulnerable repositories for language {}".format(language))
    #     for repository in configurations["vulnerable"][language]:
    #         print_info("Updating vulnerable repository: {}".format( repository))
    #         multiprocess_worker(update_git_repositories, (True, language, repository))
            

    # # update non-vulnerable repositories
    # for language in configurations["non-vulnerable"]:
    #     print_info("Updating non-vulnerable repositories for language {}".format(language))
    #     for repository in configurations["non-vulnerable"][language]:
    #         print_info("Updating non-vulnerable repository: {}".format(repository))
    #         multiprocess_worker(update_git_repositories, (False, language, repository))
    
    print_info("Git repositories updated successfully")

    # run shiftleft scan on vulnerable repositories
    # for language in configurations["vulnerable"]:  
    #     print_info("Running shiftleft scan on vulnerable repositories for language {}".format(language))
    #     for repository in configurations["vulnerable"][language]:
    #         print_info("Running shiftleft scan on vulnerable repository: {}".format(repository))
    #         multiprocess_worker(run_shiftleft_scan, (True, language, repository))
    #         # initial test break early
    #         break
    
    # run shiftleft scan on non-vulnerable repositories
    # for language in configurations["non-vulnerable"]:
    #     print_info("Running shiftleft scan on non-vulnerable repositories for language {}".format(language))
    #     for repository in configurations["non-vulnerable"][language]:
    #         print_info("Running shiftleft scan on non-vulnerable repository: {}".format(repository))
    #         multiprocess_worker(run_shiftleft_scan, (False, language, repository))
    
    

    # print_info("Shiftleft scan completed successfully")
    # for shiftleft_report in glob.glob('./repositories/*/*/*/reports', recursive=True):
    #     vulnerable = shiftleft_report.split("/")[2]
    #     language = shiftleft_report.split("/")[3]
    #     repository = shiftleft_report.split("/")[4]
    #     os.system("rm -rf scan_results/shiftleft_scan/" + vulnerable + "/" + language + "/" + repository)
    #     os.system("mkdir -p scan_results/shiftleft_scan/" + vulnerable + "/" + language + "/" + repository)
    #     os.system("mv " + shiftleft_report + "/* scan_results/shiftleft_scan/" + vulnerable + "/" + language + "/" + repository + "/")

    print_info("starting codeql scan")
    # list_of_compiled_languages= os.popen('''docker run --rm --name codeql-container -it --entrypoint /bin/bash mcr.microsoft.com/cstsectools/codeql-container -c "codeql resolve languages"''').read().split("\n")[:-1]
    code_ql_languages = {
        "JS_TS": "javascript",
        "Python": "python",
        "Java": "java",
        "Kotlin": "java",
        "C_CPP": "cpp",
        "Csharp": "csharp",
        "Ruby": "ruby",
        "Go": "go",
        # 'html': "",
        # 'csv': "",
        # 'xml': "",
        # 'properties': ""
    }

    # run codeql scan on vulnerable repositories
    for language in configurations["vulnerable"]:
        print_info("Running codeql scan on vulnerable repositories for language {}".format(language))
        for repository in configurations["vulnerable"][language]:
            print_info("Running codeql scan on vulnerable repository: {}".format(repository))
            multiprocess_worker(run_codeql_scan, (True, language, code_ql_languages[language], repository))
            # initial test break early
            break

    

    
    while True:
        for process in processes:
            if not process.is_alive():
                processes.remove(process)
        if not processes:
            break
        time.sleep(0.1)