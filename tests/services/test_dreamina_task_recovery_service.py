from app.providers.image.dreamina_cli_client import DreaminaCliClient
from app.services.dreamina_task_recovery_service import DreaminaTaskRecoveryService


class FakeRunner:
    def __init__(self, stdout):
        self.stdout = stdout
        self.calls = []

    def __call__(self, command, cwd, capture_output, text, encoding, errors, check, timeout):
        self.calls.append(command)

        class Result:
            pass

        result = Result()
        result.stdout = self.stdout
        result.stderr = ""
        result.returncode = 0
        return result


def test_dreamina_task_recovery_service_queries_submit_id(tmp_path):
    runner = FakeRunner(stdout='{"submit_id":"submit-1","gen_status":"success"}')
    client = DreaminaCliClient(
        cli_path="dreamina",
        output_dir=str(tmp_path),
        runner=runner,
        timeout_seconds=10,
    )
    service = DreaminaTaskRecoveryService(client=client)

    result = service.query_submit_id("submit-1")

    assert result["submit_id"] == "submit-1"
    assert result["gen_status"] == "success"
    assert runner.calls[0][:2] == ["dreamina", "query_result"]
    assert "--submit_id" in runner.calls[0]
    assert "--download_dir" in runner.calls[0]
