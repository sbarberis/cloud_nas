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


@app.get('/')
async def index(request: Request, current_user: Annotated[str, Depends(check_cookie)]):
    if not current_user:
        return RedirectResponse('/login', status_code=303)
    else:
        return templates.TemplateResponse(
            request=request, name="index.html", context={'current_user': current_user}
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True, use_colors=False)
