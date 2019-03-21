from django.test import TestCase
from .models import Printer, Check
import json


# Create your tests here.
class CheckTestCase(TestCase):
    def setUp(self):
        self.printer1 = Printer.objects.create(name="test_first_1", api_key="1111", check_type="kitchen", point_id=1)
        self.printer2 = Printer.objects.create(name="test_second_1", api_key="aaaa", check_type="client", point_id=1)
        self.test_request_json ={
            "id": 100500,
            "price": 200,
            "items": [
                {
                    "name": "Бургер",
                    "quantity": 1,
                    "unit_price": 200
                }
              ],
            "address": "г. Уфа, ул. Авроры, д. 25",
            "client": {
                "name": "Павел",
                "phone": 9173331234
            },
            "point_id": 1
        }

    def test_create_checks_success(self):
        response = self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                                    content_type="application/json")

        self.assertEqual(response.status_code, 200, "Error!")

    def test_create_checks_validation_error(self):
        del self.test_request_json["price"]
        self.test_request_json["items"][0]["quantity"] = "1000000"
        self.test_request_json["point_id"] = "abcd"
        response = self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                                    content_type="application/json")

        self.assertEqual(response.status_code, 400, "Error!")

    def test_create_checks_invalid_printer(self):
        self.test_request_json["point_id"] = 5
        response = self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                                    content_type="application/json")

        self.assertEqual(response.status_code, 400, "Error!")

    def test_create_checks_already_exist(self):
        self.test_request_json["id"] = 500100
        self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                         content_type="application/json")

        response = self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                                    content_type="application/json")
        self.assertEqual(response.status_code, 400, "Error!")

    def test_new_checks_auth_error(self):
        self.test_request_json["id"] = 900100
        self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                         content_type="application/json")
        response = self.client.get("/new_checks/?api_key=7899")
        self.assertEqual(response.status_code, 401, "Error!")

    def test_new_checks_success(self):
        self.test_request_json["id"] = 500800
        self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                         content_type="application/json")
        response = self.client.get("/new_checks/?api_key=aaaa")
        self.assertEqual(response.status_code, 200, "Error!")

    def test_check_omit_api_key(self):
        response = self.client.get("/check/?check_id=1")
        self.assertEqual(response.status_code, 400, "Error!")

    def test_check_omit_check_id(self):
        response = self.client.get("/check/?api_key=1111")
        self.assertEqual(response.status_code, 400, "Error!")

    def test_check_invalid_api_key(self):
        self.test_request_json["id"] = 8888999
        self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                         content_type="application/json")
        response = self.client.get("/check/?api_key=hello&check_id=2")
        self.assertEqual(response.status_code, 401, "Error!")

    def test_check_not_exists(self):
        response = self.client.get("/check/?api_key=aaaa&check_id=9000")
        self.assertEqual(response.status_code, 400, "Error!")

    def test_check_pdf_file_is_not_yet_created(self):
        self.test_request_json["id"] = 777345
        self.client.post("/create_checks/", data=json.dumps(self.test_request_json),
                         content_type="application/json")
        check_id =  Check.objects.all().order_by("id")[0].id

        response = self.client.get("/check/?api_key=aaaa&check_id={}".format(check_id))
        self.assertEqual(response.status_code, 400, "Error!")





