from fastapi import APIRouter

from app.api.routers import admin, agents, analysis, auth, career_paths, chat, files, graph, interviews, jobs, matching, ocr, reports, scheduler, student_profiles, students, teacher

api_router = APIRouter(redirect_slashes=False)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(students.router, prefix="/students", tags=["students"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(student_profiles.router, prefix="/student-profiles", tags=["student-profiles"])
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(career_paths.router, prefix="/career-paths", tags=["career-paths"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(teacher.router, prefix="/teacher", tags=["teacher"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
