from server_acceptance.models import Inventory, Expectation
from server_acceptance.reporters import build_report
def test_report_shape():
    r=build_report(Inventory(), Expectation(), []); assert all(k in r for k in ("run_id","timestamp","hostname","inventory","expectations","validation_results","overall_status"))
