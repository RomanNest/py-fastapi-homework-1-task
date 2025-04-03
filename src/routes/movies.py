from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas import MovieListResponseSchema, MovieDetailResponseSchema
from src.database.models import MovieModel
from src.database.session import get_db


router = APIRouter()


@router.get("/movies", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db),
):
    params = (page - 1) * per_page
    query = select(MovieModel).offset(params).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")
    total_movies = await db.scalar(
        select(func.count(MovieModel.id)).select_from(MovieModel)
    )
    total_pages = ceil(total_movies / per_page)

    if not total_movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    return {
        "movies": [MovieDetailResponseSchema.from_orm(movie) for movie in movies],
        "prev_page": (
            f"/movies/?page={page - 1}&per_page={per_page}"
            if page > 1 else None
        ),
        "next_page": (
            f"/movies/?page={page + 1}&per_page={per_page}"
            if page < total_pages else None
        ),
        "total_pages": total_pages,
        "total_items": total_movies,
    }


@router.get("/movies/{movie_id}", response_model=MovieDetailResponseSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await (
        db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    )
    film = result.scalar_one_or_none()
    if not film:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found.",
        )
    return film
