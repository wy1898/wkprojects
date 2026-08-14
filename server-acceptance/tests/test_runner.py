from server_acceptance.services.runner import CommandRunner
def test_missing_command(): assert CommandRunner().run(["definitely-not-a-command"]).status == "UNAVAILABLE"
