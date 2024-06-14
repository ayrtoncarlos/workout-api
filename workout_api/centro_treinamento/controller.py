from fastapi import APIRouter, Body, HTTPException, status
from fastapi_pagination import LimitOffsetPage, paginate
from pydantic import UUID4
from sqlalchemy import select
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.centro_treinamento.schemas import CentroTreinamentoIn, CentroTreinamentoOut
from workout_api.contrib.dependencies import DatabaseDependency
from uuid import uuid4


router = APIRouter()


@router.post(
    path="/",
    summary="Criar um novo Centro de Treinamento",
    status_code=status.HTTP_201_CREATED,
    response_model=CentroTreinamentoOut
)
async def post(
        db_session: DatabaseDependency,
        centro_treinamento_in: CentroTreinamentoIn = Body(...)
) -> CentroTreinamentoOut:
    centro_treinamento_out = CentroTreinamentoOut(id=uuid4(), **centro_treinamento_in.model_dump())
    centro_treinamento_model = CentroTreinamentoModel(**centro_treinamento_out.model_dump())

    db_session.add(centro_treinamento_model)
    await db_session.commit()

    return centro_treinamento_out


@router.get(
    path="/",
    summary="Consultar todos os Centros de Treinamento",
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[CentroTreinamentoOut]
)
async def get_all(db_session: DatabaseDependency) -> LimitOffsetPage[CentroTreinamentoOut]:
    centros_treinamento: list[CentroTreinamentoOut] = ((await db_session.execute(
        select(CentroTreinamentoModel)))
                    .scalars().all()
    )

    return paginate(centros_treinamento)


@router.get(
    path="/{id}",
    summary="Consultar um Centro de Treinamento pelo id",
    status_code=status.HTTP_200_OK,
    response_model=CentroTreinamentoOut
)
async def get_by_id(id: UUID4, db_session: DatabaseDependency) -> CentroTreinamentoOut:
    centro_treinamento: CentroTreinamentoOut = ((await db_session.execute(
        select(CentroTreinamentoModel).filter_by(id=id)))
                    .scalars().first()
    )

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Centro de Treinamento não encontrado no id: {id}."
        )

    return centro_treinamento
