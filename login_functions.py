from fastapi import FastAPI, Header, Form, APIRouter, HTTPException, status, Cookie
from typing import Annotated
from pydantic import BaseModel, Field
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import timezone
import datetime
import jwt
import json


login_router = APIRouter()
templates = Jinja2Templates(directory="templates")


class FormData(BaseModel):
    email: str
    password: str


def load_configs() -> dict:
    with open('./config.json') as json_file:
        data = json.load(json_file)
    return data


def decode_jwt_data(token: str):
    try:
        decoded_data = jwt.decode_complete(token, load_configs()['key'], algorithms=["HS512"])
    except (jwt.exceptions.InvalidSignatureError,
            jwt.exceptions.DecodeError,
            jwt.exceptions.ExpiredSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return decoded_data['payload']['user']


def encode_jwt_data(payload: str) -> str:
    encoded_jwt = jwt.encode(
        {"user": payload,
         "exp": datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(hours=8),
         "nbf": datetime.datetime.now(tz=timezone.utc),
         "iss": "vg.api"
         },
        load_configs()['key'],
        algorithm="HS512")

    return encoded_jwt


@login_router.get('/logout')
def logout():
    response = RedirectResponse('/login', status_code=303)
    response.delete_cookie('user_session')

    return response


@login_router.post('/auth')
async def auth(form_data: Annotated[FormData, Form()]):
    response = RedirectResponse(url='/', status_code=303)
    jwt_token = encode_jwt_data(form_data.email)

    response.set_cookie(
        key="user_session",
        value=jwt_token,
        max_age=14400
    )

    return response


