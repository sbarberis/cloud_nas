from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated
from mysql_functions import MySqlDataInterface
from login_functions import login_router, check_cookie
from file_on_server import file_on_server_router

import uvicorn
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import locale

EXCLUDED_FILES = ['.DS_Store']


class Settings(BaseSettings):
    project_id: str
    bucket_name: str
    firestore_repo: str
    documents_collection: str
    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
mysql_interface = MySqlDataInterface()
app = FastAPI(title="Cloud NAS", description="NAS swagger app")

app.include_router(login_router)
app.include_router(file_on_server_router)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def _format_number(number: int) -> str:
    locale.setlocale(locale.LC_ALL, 'it_IT')
    return locale.format_string('%.0f', number, True)


@app.get('/')
async def index(request: Request, current_user: Annotated[str, Depends(check_cookie)]):
    if not current_user:
        return RedirectResponse('/login', status_code=303)
    else:

        file_on_server_count = _format_number(mysql_interface.fetch_file_on_server_count())
        file_on_tape_count = _format_number(mysql_interface.fetch_file_on_tape_count())

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={'current_user': current_user,
                     'file_on_server_count': file_on_server_count,
                     'file_on_tape_count': file_on_tape_count}
        )


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 405:
        return RedirectResponse("/method_not_allowed", status_code=303)
    elif exc.status_code == 404:
        return RedirectResponse("/page_not_found", status_code=303)
    return RedirectResponse("/generic_error", status_code=303)


@app.get("/method_not_allowed")
async def page_not_found(request: Request):
    return templates.TemplateResponse(
        request=request, name="errors/405.html"
    )


@app.get("/page_not_found")
async def page_not_found(request: Request):
    return templates.TemplateResponse(
        request=request, name="errors/404.html"
    )


@app.get("/generic_error")
async def generic_error(request: Request):
    return templates.TemplateResponse(
        request=request, name="errors/500.html"
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True, use_colors=False)
