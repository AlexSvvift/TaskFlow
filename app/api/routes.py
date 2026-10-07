from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Client, Order, User
from app.schemas import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    DashboardResponse,
    HealthResponse,
    LoginRequest,
    OrderCreate,
    OrderResponse,
    OrderStatus,
    OrderUpdate,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)

router = APIRouter(prefix="/api")


def get_session(request: Request) -> Generator[Session, None, None]:
    with request.app.state.session_factory() as session:
        yield session


def _user_response(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


def _order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        client_id=order.client_id,
        created_by_id=order.created_by_id,
        title=order.title,
        description=order.description,
        status=order.status,
        amount=order.amount,
        client_name=order.client.name if order.client else None,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(status="ok", service=request.app.state.settings.app_name)


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, session: Session = Depends(get_session)):
    email = str(payload.email).lower()
    if session.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")

    first_user = session.scalar(select(User.id).limit(1)) is None
    user = User(
        email=email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role="admin" if first_user else "manager",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    token = create_access_token(
        user,
        request.app.state.settings.secret_key,
        request.app.state.settings.access_token_expire_minutes,
    )
    return TokenResponse(access_token=token, user=_user_response(user))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, session: Session = Depends(get_session)):
    email = str(payload.email).lower()
    user = session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = create_access_token(
        user,
        request.app.state.settings.secret_key,
        request.app.state.settings.access_token_expire_minutes,
    )
    return TokenResponse(access_token=token, user=_user_response(user))


@router.get("/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return _user_response(user)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
) -> DashboardResponse:
    del user
    total_orders = session.scalar(select(func.count(Order.id))) or 0
    new_orders = session.scalar(select(func.count(Order.id)).where(Order.status == OrderStatus.NEW.value)) or 0
    active_orders = session.scalar(
        select(func.count(Order.id)).where(Order.status == OrderStatus.IN_PROGRESS.value)
    ) or 0
    completed_orders = session.scalar(
        select(func.count(Order.id)).where(Order.status == OrderStatus.DONE.value)
    ) or 0
    revenue = session.scalar(
        select(func.coalesce(func.sum(Order.amount), 0)).where(Order.status == OrderStatus.DONE.value)
    ) or 0
    return DashboardResponse(
        total_clients=session.scalar(select(func.count(Client.id))) or 0,
        total_orders=total_orders,
        new_orders=new_orders,
        active_orders=active_orders,
        completed_orders=completed_orders,
        total_revenue=round(float(revenue), 2),
    )


@router.get("/clients", response_model=list[ClientResponse])
def list_clients(
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    del user
    return list(session.scalars(select(Client).order_by(Client.id.desc())).all())


@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    del user
    client = Client(**payload.model_dump())
    session.add(client)
    session.commit()
    session.refresh(client)
    return client


@router.patch("/clients/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    del user
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    session.commit()
    session.refresh(client)
    return client


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(require_admin),
):
    del user
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    session.delete(client)
    session.commit()


@router.get("/orders", response_model=list[OrderResponse])
def list_orders(
    order_status: OrderStatus | None = None,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    del user
    statement = select(Order).options(joinedload(Order.client)).order_by(Order.id.desc())
    if order_status is not None:
        statement = statement.where(Order.status == order_status.value)
    return [_order_response(order) for order in session.scalars(statement).all()]


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    client = session.get(Client, payload.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    order_data = payload.model_dump()
    order_data["status"] = payload.status.value
    order = Order(**order_data, created_by_id=user.id)
    session.add(order)
    session.commit()
    session.refresh(order)
    order.client = client
    return _order_response(order)


@router.patch("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    del user
    order = session.scalar(select(Order).options(joinedload(Order.client)).where(Order.id == order_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value.value if isinstance(value, OrderStatus) else value)
    session.commit()
    session.refresh(order)
    return _order_response(order)


@router.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(require_admin),
):
    del user
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    session.delete(order)
    session.commit()
