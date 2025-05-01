from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

chart_router = APIRouter()


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
