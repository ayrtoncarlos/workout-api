from datetime import datetime, timezone
from fastapi import APIRouter, Body, status, HTTPException
from fastapi_pagination import LimitOffsetPage, paginate
from pydantic import UUID4
from sqlalchemy import select
from workout_api.atleta.models import AtletaModel
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency
from uuid import uuid4


router = APIRouter()


@router.post(
    path="/",
    summary="Criar um novo Atleta",
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut
)
async def post(
        db_session: DatabaseDependency,
        atleta_in: AtletaIn = Body(...)
) -> AtletaOut:
    categoria_name = atleta_in.categoria.nome
    centro_treinamento_nome = atleta_in.centro_treinamento.nome

    categoria = ((await db_session.execute(
        select(CategoriaModel).filter_by(nome=categoria_name)))
                 .scalars().first()
    )

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A categoria '{categoria_name}' não foi encontrada."
        )

    centro_treinamento = ((await db_session.execute(
        select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_nome)))
                 .scalars().first()
                 )

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O centro de treinamento '{centro_treinamento_nome}' não foi encontrado."
        )

    try:
        atleta_out = AtletaOut(
            id=uuid4(),
            create_at=datetime.now(timezone.utc).replace(tzinfo=None),
            **atleta_in.model_dump()
        )
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={"categoria", "centro_treinamento"}))
        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id

        db_session.add(atleta_model)
        await db_session.commit()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao inserir os dados no banco."
        )

    return atleta_out


@router.get(
    path="/",
    summary="Consultar todos os Atletas",
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[AtletaOut]
)
async def get_all(db_session: DatabaseDependency) -> LimitOffsetPage[AtletaOut]:
    atletas: list[AtletaOut] = ((await db_session.execute(
        select(AtletaModel)))
                .scalars().all()
    )

    lista_atletas = [AtletaOut.model_validate(atleta) for atleta in atletas]

    return paginate(lista_atletas)


@router.get(
    path="/{id}",
    summary="Consultar um Atleta pelo id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut
)
async def get_by_id(id: UUID4, db_session: DatabaseDependency) -> AtletaOut:
    atleta: AtletaOut = ((await db_session.execute(
        select(AtletaModel).filter_by(id=id)))
                    .scalars().first()
    )

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrado no id: {id}."
        )

    return atleta


@router.patch(
    path="/{id}",
    summary="Editar um Atleta pelo id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut
)
async def patch(id: UUID4, db_session: DatabaseDependency, atleta_update: AtletaUpdate = Body(...)) -> AtletaOut:
    atleta: AtletaOut = ((await db_session.execute(
        select(AtletaModel).filter_by(id=id)))
                    .scalars().first()
    )

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrado no id: {id}."
        )

    atleta_up = atleta_update.model_dump(exclude_unset=True)

    for key, value in atleta_up.items():
        setattr(atleta, key, value)

    db_session.commit()
    db_session.refresh(atleta)

    return atleta


@router.delete(
    path="/{id}",
    summary="Deletar um Atleta pelo id",
    status_code=status.HTTP_204_NO_CONTENT
)
async def get_by_id(id: UUID4, db_session: DatabaseDependency) -> None:
    atleta: AtletaOut = ((await db_session.execute(
        select(AtletaModel).filter_by(id=id)))
                    .scalars().first()
    )

    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Atleta não encontrado no id: {id}."
        )

    db_session.delete(atleta)
    db_session.commit()
