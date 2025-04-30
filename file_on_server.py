from fastapi import  Request, HTTPException, Form, Cookie, Depends, APIRouter
from fastapi.templating import Jinja2Templates

import login_functions
from typing import Annotated
from mysql_functions import MySqlDataInterface

from typing import Tuple, Any
from fastapi.responses import RedirectResponse
from pydantic import BaseModel


mysql_interface = MySqlDataInterface()
templates = Jinja2Templates(directory="templates")

file_on_server_router = APIRouter()


class FormSearch(BaseModel):
    file_name: str | None = None
    offset: str


def check_cookie(user_session: Annotated[str | None, Cookie()] = None) -> Any:

    try:
        current_user = login_functions.decode_jwt_data(user_session)
    except HTTPException:
        return None
    if not user_session:
        return None
    return current_user


@file_on_server_router.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(
        request=request, name="login.html", context={"item_id": "1"}
    )


@file_on_server_router.get('/datatables/{offset}')
async def datatables(request: Request, offset: int, current_user: Annotated[str, Depends(check_cookie)]):
    if not current_user:
        return RedirectResponse('/login', status_code=303)

    file_su_server = mysql_interface.fetch_file_su_server(None, offset=offset, limit=20)

    total_size = mysql_interface.fetch_file_su_server(
        None,
        offset=0)

    last_page_offset = len(total_size) - 20

    prev_data, next_data = update_prev_next(offset)

    current_page = (next_data / 20) + 1 if next_data % 20 > 0 else (next_data / 20)
    total_pages = (len(total_size) // 20) + 1 if len(total_size) % 20 > 0 else len(total_size) / 20

    print(len(total_size))
    print(int(current_page))
    print(total_pages)

    return templates.TemplateResponse(
        request=request,
        name="tables/datatables.html",
        context={
            'file_su_server': file_su_server,
            'prev': prev_data, 'next': next_data,
            'current_user': current_user,
            'last_page_offset': last_page_offset,
            'total_size': len(total_size),
            'current_page': int(current_page),
            'total_pages': total_pages
        },
    )


@file_on_server_router.post('/data_paging')
async def data_paging(
        request: Request,
        form_search: Annotated[FormSearch, Form()],
        current_user: Annotated[str, Depends(check_cookie)]):

    if not current_user:
        return RedirectResponse('/login', status_code=303)

    file_su_server = mysql_interface.fetch_file_su_server(
        form_search,
        offset=int(form_search.offset),
        limit=20)

    total_size = mysql_interface.fetch_file_su_server(
        form_search,
        offset=0)

    last_page_offset = len(total_size)-20

    prev_data, next_data = update_prev_next(int(form_search.offset))

    current_page = (next_data / 20) + 1 if next_data % 20 > 0 else (next_data / 20)
    total_pages = (len(total_size) // 20) + 1 if len(total_size) % 20 > 0 else len(total_size) / 20

    print(len(total_size))
    print(int(current_page))
    print(total_pages)

    return templates.TemplateResponse(
        request=request,
        name="tables/datatables.html",
        context={
            'file_su_server': file_su_server,
            'prev': prev_data,
            'next': next_data,
            'current_user': current_user,
            'file_name': form_search.file_name,
            'last_page_offset': last_page_offset,
            'total_size': len(total_size),
            'current_page': int(current_page),
            'total_pages': total_pages
        }
    )


def update_prev_next(offset: int) -> Tuple[int, int]:
    prev_data = offset
    if offset == 0:
        prev_data = 0
        next_data = 20
    else:
        next_data = prev_data + 20
        prev_data = prev_data - 20

    return prev_data, next_data
