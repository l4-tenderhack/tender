from fastapi import APIRouter

from app.api.v1.endpoints import auth, cte, nmck, parsing, search, system, generate_doc, cte_search


api_router = APIRouter()
api_router.include_router(system.router, tags=["system"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(parsing.router, tags=["parsing"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(cte.router, tags=["cte"])
api_router.include_router(cte_search.router, tags=["cte-search"])
api_router.include_router(generate_doc.router, tags=["generate_doc"])
api_router.include_router(nmck.router, tags=["nmck"])
