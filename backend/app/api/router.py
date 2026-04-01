from fastapi import APIRouter

from app.api.routers import agents, auth, career_paths, files, graph, jobs, matching, ocr, reports, scheduler, student_profiles

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(student_profiles.router, prefix="/student-profiles", tags=["student-profiles"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(career_paths.router, prefix="/career-paths", tags=["career-paths"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])

