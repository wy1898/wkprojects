from server_acceptance.models import Inventory, Expectation
from server_acceptance.validators import ValidationEngine
def test_gpu_count_fail():
    r=ValidationEngine().validate(Inventory(gpu={"gpus":[1,2,3]}), Expectation({"gpu_count":{"exact":4}})); assert r[0].status.value == "FAIL"
def test_gpu_count_pass():
    r=ValidationEngine().validate(Inventory(gpu={"gpus":[1,2,3,4]}), Expectation({"gpu_count":{"exact":4}})); assert r[0].status.value == "PASS"
def test_minimum_allows_more():
    r=ValidationEngine().validate(Inventory(gpu={"gpus":[1,2,3,4,5]}), Expectation({"gpu_count":{"min":4}})); assert r[0].status.value == "PASS"
def test_minimum_rejects_less():
    r=ValidationEngine().validate(Inventory(gpu={"gpus":[1,2,3]}), Expectation({"gpu_count":{"min":4}})); assert r[0].status.value == "FAIL"
def test_exact_rejects_more():
    r=ValidationEngine().validate(Inventory(gpu={"gpus":[1,2,3,4,5]}), Expectation({"gpu_count":{"exact":4}})); assert r[0].status.value == "FAIL"
def test_legacy_integer_is_minimum():
    r=ValidationEngine().validate(Inventory(gpu={"gpus":[1,2,3,4,5]}), Expectation({"gpu_count":4})); assert r[0].status.value == "PASS"
def test_unavailable_is_not_fail():
    r=ValidationEngine().validate(Inventory(gpu={"status":"UNAVAILABLE"}), Expectation({"gpu_count":4})); assert r[0].status.value == "UNAVAILABLE"
