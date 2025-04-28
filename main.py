from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Form, status, Response, Cookie, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import login_functions
from firestore_functions import FirestoreMngr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated
from storage_functions import BucketMngr
from datetime import datetime
from mysql_functions import MySqlDataInterface
from login_functions import login_router

import uvicorn
import ffmpeg
import os
from typing import Tuple, Any
from fastapi.responses import RedirectResponse

EXCLUDED_FILES = ['.DS_Store']


class Settings(BaseSettings):
    project_id: str
    bucket_name: str
    firestore_repo: str
    documents_collection: str
    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()

app = FastAPI(title="Cloud NAS", description="NAS swagger app")
app.include_router(login_router)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

firestore_instance = FirestoreMngr(settings.project_id, settings.firestore_repo)
bucket_mngr = BucketMngr(settings.project_id, settings.bucket_name)


@app.get("/download")
async def download():
    headers = {'Content-Disposition': 'attachment; filename="images.png"'}
    return FileResponse('images.png', headers=headers)


def create_document(name: str, file_name: str):
    return {
        'name': name,
        'file_name': file_name,
        'upload_date': datetime.now().strftime('%Y-%m-%d')
    }


def check_cookie(user_session: Annotated[str | None, Cookie()] = None) -> Any:

    try:
        current_user = login_functions.decode_jwt_data(user_session)
    except HTTPException:
        return None
    if not user_session:
        return None
    return current_user


@app.get('/')
async def index(request: Request, current_user: Annotated[str, Depends(check_cookie)]):
    if not current_user:
        return RedirectResponse('/login', status_code=303)
    else:
        return templates.TemplateResponse(
            request=request, name="index.html", context={'current_user': current_user}
        )


@app.post("/upload")
async def upload(upload_file: Annotated[UploadFile, File()], name: Annotated[str, Form()]):
    try:
        file_content = upload_file.file.read()
        with open(upload_file.filename, 'wb') as f:
            f.write(file_content)

        bucket_mngr.upload_blob(upload_file.filename, upload_file.filename)

        firestore_instance.create_document_with_id('documents', create_document(name=name,
                                                                                file_name=upload_file.filename))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Something went wrong {e}')
    finally:
        upload_file.file.close()

    return {"message": f"Successfully uploaded {upload_file.filename}"}


@app.post("/create/documents")
async def create_documents():
    for index in range(10):
        document = {
            'index': index,
            'name': f"document {index}"
        }
        firestore_instance.create_document_with_id('documents', document, f"document{index}")
    return "completed"


@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={"item_id": "1"}
    )


@app.get("/pagination/{direction}")
async def page_result(direction: str, start_from: str | None = None):
    if start_from:
        doc = firestore_instance.get_document_by_id('documents', start_from)
        if direction == 'forward':
            documents = firestore_instance.get_collection('documents').order_by('index').start_after(doc).limit(3)
        else:
            documents = firestore_instance.get_collection('documents').order_by('index',
                                                                                direction='DESCENDING').start_after(
                doc).limit(3)
    else:
        documents = firestore_instance.get_collection('documents').order_by('index').limit(3)

    doclist = list(documents.stream())

    for document in list(reversed(doclist)):
        print(document.id)


@app.get('/datatables/{offset}')
async def datatables(request: Request, offset: int, current_user: Annotated[str, Depends(check_cookie)]):
    if not current_user:
        return RedirectResponse('/login', status_code=303)

    mysql_interface = MySqlDataInterface()
    file_su_server = mysql_interface.fetch_file_su_server(offset=offset, limit=20)

    prev_data, next_data = update_prev_next(offset)

    return templates.TemplateResponse(
        request=request,
        name="tables/datatables.html",
        context={'file_su_server': file_su_server, 'prev': prev_data, 'next': next_data, 'current_user': current_user}
    )


@app.get("/set-cookie/")
def create_cookie(response: Response):
    response.set_cookie(
        key="usersession",
        value="{'id': '123', 'user': 'username@mail.com'}",
        max_age=10
    )
    return {"message": "Come to the dark side, we have cookies"}


@app.get("/verify")
def verify_login(cookie: Annotated[str, Depends(check_cookie)]):
    print(cookie)


def update_prev_next(offset: int) -> Tuple[int, int]:
    prev_data = offset
    if offset == 0:
        prev_data = 0
        next_data = 20
    else:
        next_data = prev_data + 20
        prev_data = prev_data - 20

    return prev_data, next_data


@app.get("/load-metadata-from-url")
async def get_metadata(filepath: str):
    metadata = []

    for f in os.listdir(filepath):
        if f not in EXCLUDED_FILES:
            full_path = f"{filepath}{f}"
            metadata.append(load_metadata_from_file(full_path))

    return metadata


def load_metadata_from_file(filepath: str) -> dict:
    metadata = None
    try:
        metadata = ffmpeg.probe(filename=f"{filepath}", cmd='/opt/homebrew/bin/ffprobe')
    except ffmpeg.Error as e:
        print(f'Error {e}')

    return metadata


@app.get('/users')
async def get_users():
    mysql_interface = MySqlDataInterface()
    users = mysql_interface.fetch_all_users()

    for row in users:
        print(row['ut_username'])
    return 'OK'


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True, use_colors=False)
