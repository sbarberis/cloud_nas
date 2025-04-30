from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def chart(request: Request):
    labels = ["Gennaio", "Febbraio", "Marzo"]
    values = [30, 10, 60]
    values2 = [10, 15, 50]

    return templates.TemplateResponse("chart.html", {
        "request": request,
        "labels": labels,
        "values": values,
        "values2": values2
    })
