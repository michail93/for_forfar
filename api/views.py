from django.shortcuts import render

# Create your views here.

from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django_rq import enqueue
import json
from base64 import b64encode
from django.core.exceptions import ValidationError
from jsonschema import validate
from jsonschema import exceptions as js_schema_ex

from forfar.settings import BASE_DIR
from django.views.decorators.csrf import csrf_exempt
from .models import Printer, Check


import requests
import os


def async_pdf_creation(check_type, order, check_id):
    """
    Таск, который кладется в очередь
    """
    order["check_type"] = check_type

    render_str = render_to_string("api/template_check.html", context={
        "context": order
    })

    base64_bytes = b64encode(bytes(render_str, encoding="utf-8"))
    base64_string = base64_bytes.decode('utf-8')

    data = {
        'contents': base64_string,
    }
    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.post('http://localhost:8080', data=json.dumps(data), headers=headers)

    save_path = os.path.join(BASE_DIR, "media/pdf/{}_{}.pdf".format(order["id"], check_type))

    with open(save_path, "wb") as pdf:
        pdf.write(response.content)

    Check.objects.filter(id=check_id).update(status="rendered")


@csrf_exempt
def create_checks(request):
    """
    Создает чеки для заказа, переданного в JSON внутри тела http запроса
    """

    if request.method != "POST":
        response = JsonResponse({"error": "Not allowed method"})
        response.status_code = 403
        return response

    try:
        js_request = json.loads(request.body)
    except json.JSONDecodeError:
        response = JsonResponse({
            "error": "Invalid JSON"
        })
        response.status_code = 400
        return response

    # Проверка соответствия JSON указанной схеме
    # при помощи jsonschema
    if not json_validate(js_request):
        response = JsonResponse({
            "error": "ValidationError, either not enough required properties or not valid type of required properties"
        })
        response.status_code = 400
        return response

    # print(js_request["id"])

    if Printer.objects.filter(point_id=js_request["point_id"]).count() == 0:
        response = JsonResponse({
            "error": "Для данной точки не настроено ни одного принтера"
        })
        response.status_code = 400
        return response

    # print(Check.objects.filter(order__id=js_request["id"]).count())

    if Check.objects.filter(order__id=js_request["id"]).count() > 0:
        response = JsonResponse({
            "error": "Для данного заказа уже созданы чеки"
        })
        response.status_code = 400
        return response

    client_printer = Printer.objects.filter(point_id=js_request["point_id"]).filter(check_type="client")[0]
    kitchen_printer = Printer.objects.filter(point_id=js_request["point_id"]).filter(check_type="kitchen")[0]

    # print(kitchen_printer.check_type, client_printer.check_type)

    pdf_client_file_path = os.path.join(BASE_DIR, "media/pdf/{}_{}.pdf".format(js_request["id"],"client"))
    pdf_kitchen_file_path = os.path.join(BASE_DIR, "media/pdf/{}_{}.pdf".format(js_request["id"],"kitchen"))

    # print(pdf_client_file_path)

    client_check = Check(printer_id=client_printer, type=client_printer.check_type, order=js_request, status="new",
                      pdf_file=pdf_client_file_path)

    kitchen_check = Check(printer_id=kitchen_printer, type=kitchen_printer.check_type, order=js_request, status="new",
                      pdf_file=pdf_kitchen_file_path)

    try:
        client_check.full_clean()
    except ValidationError:
        response = JsonResponse({
            "error": "error"
        })
        response.status_code = 400
        return response

    try:
        kitchen_check.full_clean()
    except ValidationError:
        response = JsonResponse({
            "error": "error"
        })
        response.status_code = 400
        return response

    client_check.save()
    kitchen_check.save()

    # print(client_check.pk, kitchen_check.pk)

    enqueue(async_pdf_creation, client_printer.check_type, js_request, client_check.pk)
    enqueue(async_pdf_creation, kitchen_printer.check_type, js_request, kitchen_check.pk)

    return JsonResponse({"ok": "Чеки успешно созданы"})


def new_checks(request):
    """
    Возвращает список чеков доступных для печати
    """

    if request.method != "GET":
        response = JsonResponse({"error": "Not allowed method"})
        response.status_code = 403
        return response

    try:
        request.GET["api_key"]
    except KeyError:
        response = JsonResponse({
            "error": "There isn't querystring(api_key)"
        })
        response.status_code = 400
        return response

    try:
        pr = Printer.objects.get(api_key=request.GET["api_key"])
    except Printer.DoesNotExist:
        response = JsonResponse({
            "error": "Ошибка авторизации"
        })
        response.status_code = 401
        return response

    checks = Check.objects.filter(printer_id=pr).filter(status="rendered")

    response = {
        "checks": []
    }

    for check in checks:
        response["checks"].append({"id": check.pk})

    return JsonResponse(response)


def check(request):
    """
    Возвращает pdf-файл чека
    """

    if request.method != "GET":
        response = JsonResponse({"error": "Not allowed method"})
        response.status_code = 403
        return response

    try:
        request.GET["api_key"]
    except KeyError:

        response = JsonResponse({
            "error": "There isn't querystring(api_key)"
        })
        response.status_code = 400
        return response

    try:
        request.GET["check_id"]
    except KeyError:

        response = JsonResponse({
            "error": "There isn't querystring(check_id)"
        })
        response.status_code = 400
        return response

    try:
        pr = Printer.objects.get(api_key=request.GET["api_key"])
    except Printer.DoesNotExist:
        response = JsonResponse({
            "error": "Ошибка авторизации"
        }, json_dumps_params={'ensure_ascii': False})
        response.status_code = 401
        return response

    try:
        ck = Check.objects.filter(printer_id=pr).get(pk=request.GET["check_id"])
    except Check.DoesNotExist:
        response = JsonResponse({
            "error": "Данного чека не существует"
        }, json_dumps_params={'ensure_ascii': False})
        response.status_code = 400
        return response

    if ck.status == "new":
        response = JsonResponse({
            "error": "Для данного чека не сгенерирован PDF-файл"
        }, json_dumps_params={'ensure_ascii': False})
        response.status_code = 400
        return response

    print(ck.pdf_file.path)

    with open(ck.pdf_file.path, "rb") as pdf:
        response = HttpResponse(pdf.read(), content_type="application/pdf")
        response["Content-Disposition"] = "inline;filename={}_{}.pdf".format(ck.order["id"], ck.type)

    Check.objects.filter(pk=ck.pk).update(status="printed")

    return response


def json_validate(js_request):
    """
    Проверяет соответствие JSON(js_request) указанной схеме(schema)
    """
    schema = {
        "type": "object",
        "properties": {
            "id": {"type": "number"},
            "price": {"type": "number"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "quantity": {
                            "type": "number"
                        },
                        "unit_price": {
                            "type": "number"
                        }
                    },
                    "required": [
                        "name", "quantity", "unit_price"
                    ]
                }
            },
            "address": {"type": "string"},
            "client": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "number"}
                },
                "required": [
                    "name", "phone"
                ]
            },
            "point_id": {"type": "number"}
        },
        "required": [
            "id", "price", "items", "address", "client", "point_id"
        ]
    }

    try:
        validate(js_request, schema)
    except js_schema_ex.ValidationError:
        return False

    return True
