from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from firestore_functions import FirestoreMngr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated
from storage_functions import BucketMngr
from datetime import datetime

import uvicorn


class Settings(BaseSettings):
    project_id: str
    bucket_name: str
    firestore_repo: str
    documents_collection: str
    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()


app = FastAPI(title="Cloud NAS", description="NAS swagger app")
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


@app.get("/pagination/{direction}")
async def page_result(direction: str, start_from: str | None = None):
    if start_from:
        doc = firestore_instance.get_document_by_id('documents', start_from)
        if direction == 'forward':
            documents = firestore_instance.get_collection('documents').order_by('index').start_after(doc).limit(3)
        else:
            documents = firestore_instance.get_collection('documents').order_by('index', direction='DESCENDING').start_after(doc).limit(3)
    else:
        documents = firestore_instance.get_collection('documents').order_by('index').limit(3)

    doclist = list(documents.stream())

    for document in list(reversed(doclist)):
        print(document.id)


def load_sample_data() -> []:
    collection = firestore_instance.get_collection('users')
    return [user.to_dict() for user in collection.stream()]


@app.get("/users", response_class=HTMLResponse)
async def show_users(request: Request):
    return templates.TemplateResponse(
        request=request, name="users.html", context={"user_list": load_sample_data()}
    )


@app.get("/user_list")
async def get_users():
    print(settings.mail_address)
    return load_sample_data()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9090, reload=True, use_colors=False)
