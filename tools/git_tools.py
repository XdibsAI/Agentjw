import subprocess

class GitTools:

    @staticmethod
    def status():
        return subprocess.check_output(
            ["git","status","--short"]
        ).decode()

    @staticmethod
    def diff():
        return subprocess.check_output(
            ["git","diff"]
        ).decode()

    @staticmethod
    def last_commit():
        return subprocess.check_output(
            ["git","log","-1","--oneline"]
        ).decode()
