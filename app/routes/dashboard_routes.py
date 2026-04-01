from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from app.database import get_db
from app.models import User, Content, Campaign, Video, ArtRequest, Idea, CalendarEvent
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    today = date.today()

    total_contents = db.query(Content).count()
    in_production = db.query(Content).filter(Content.status == "producao").count()
    posted = db.query(Content).filter(Content.status == "postado").count()
    active_campaigns = db.query(Campaign).filter(Campaign.status == "ativa").count()
    pending_arts = db.query(ArtRequest).filter(ArtRequest.status.in_(["enviado", "andamento"])).count()
    pending_videos = db.query(Video).filter(Video.status.in_(["roteiro", "gravado", "edicao"])).count()
    total_ideas = db.query(Idea).filter(Idea.is_converted == False).count()

    overdue_contents = db.query(Content).filter(
        Content.due_date < today,
        Content.status.notin_(["finalizado", "postado"])
    ).count()

    overdue_arts = db.query(ArtRequest).filter(
        ArtRequest.deadline < today,
        ArtRequest.status != "aprovado"
    ).count()

    upcoming_events = db.query(CalendarEvent).filter(
        CalendarEvent.date >= today,
        CalendarEvent.date <= today + timedelta(days=7)
    ).order_by(CalendarEvent.date).limit(5).all()

    recent_contents = db.query(Content).order_by(Content.updated_at.desc()).limit(5).all()

    contents_by_type = {}
    for row in db.query(Content.content_type, Content.status).all():
        if row.content_type not in contents_by_type:
            contents_by_type[row.content_type] = {"total": 0, "posted": 0}
        contents_by_type[row.content_type]["total"] += 1
        if row.status == "postado":
            contents_by_type[row.content_type]["posted"] += 1

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "page": "dashboard",
        "total_contents": total_contents,
        "in_production": in_production,
        "posted": posted,
        "active_campaigns": active_campaigns,
        "pending_arts": pending_arts,
        "pending_videos": pending_videos,
        "total_ideas": total_ideas,
        "overdue_contents": overdue_contents,
        "overdue_arts": overdue_arts,
        "upcoming_events": upcoming_events,
        "recent_contents": recent_contents,
        "contents_by_type": contents_by_type,
    })


@router.get("/api/dashboard/productivity", tags=["dashboard"])
async def productivity_data(weeks: int = 8, db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    """Production stats per week for the last N weeks."""
    today = date.today()
    result = {"labels": [], "created": [], "posted": [], "by_type": {}, "completion_rate": 0}

    total_created = 0
    total_posted = 0

    for i in range(weeks - 1, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7 * i)
        week_end = week_start + timedelta(days=6)
        label = f"{week_start.strftime('%d/%m')}"

        created = db.query(Content).filter(
            Content.created_at >= week_start.isoformat(),
            Content.created_at <= (week_end + timedelta(days=1)).isoformat(),
        ).count()

        posted_count = db.query(Content).filter(
            Content.status == "postado",
            Content.updated_at >= week_start.isoformat(),
            Content.updated_at <= (week_end + timedelta(days=1)).isoformat(),
        ).count()

        result["labels"].append(label)
        result["created"].append(created)
        result["posted"].append(posted_count)
        total_created += created
        total_posted += posted_count

    if total_created > 0:
        result["completion_rate"] = round((total_posted / total_created) * 100, 1)

    # By type breakdown
    for row in db.query(Content.content_type, func.count(Content.id)).group_by(Content.content_type).all():
        result["by_type"][row[0]] = row[1]

    return result


@router.get("/api/reports/pdf", tags=["reports"])
async def generate_pdf_report(month: int = None, year: int = None,
                              db: Session = Depends(get_db),
                              user: User = Depends(get_current_user)):
    """Generate a simple text-based report (CSV format for now)."""
    import calendar as cal
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year

    month_name = ["", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
                  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][month]

    first_day = date(year, month, 1)
    last_day = date(year, month, cal.monthrange(year, month)[1])

    contents = db.query(Content).filter(
        Content.created_at >= first_day.isoformat(),
        Content.created_at <= (last_day + timedelta(days=1)).isoformat(),
    ).all()

    arts = db.query(ArtRequest).filter(
        ArtRequest.created_at >= first_day.isoformat(),
        ArtRequest.created_at <= (last_day + timedelta(days=1)).isoformat(),
    ).all()

    videos = db.query(Video).filter(
        Video.created_at >= first_day.isoformat(),
        Video.created_at <= (last_day + timedelta(days=1)).isoformat(),
    ).all()

    events = db.query(CalendarEvent).filter(
        CalendarEvent.date >= first_day,
        CalendarEvent.date <= last_day,
    ).all()

    posted = [c for c in contents if c.status == "postado"]
    in_prod = [c for c in contents if c.status in ("producao", "aprovacao")]

    lines = []
    lines.append(f"RELATORIO DE PRODUTIVIDADE - {month_name} {year}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Periodo: {first_day.strftime('%d/%m/%Y')} a {last_day.strftime('%d/%m/%Y')}")
    lines.append("")
    lines.append("RESUMO GERAL")
    lines.append("-" * 40)
    lines.append(f"Conteudos criados:     {len(contents)}")
    lines.append(f"Conteudos postados:    {len(posted)}")
    lines.append(f"Em producao:           {len(in_prod)}")
    lines.append(f"Artes solicitadas:     {len(arts)}")
    lines.append(f"Videos produzidos:     {len(videos)}")
    lines.append(f"Eventos no calendario: {len(events)}")
    lines.append("")

    by_type = {}
    for c in contents:
        by_type[c.content_type] = by_type.get(c.content_type, 0) + 1
    if by_type:
        lines.append("POR TIPO DE CONTEUDO")
        lines.append("-" * 40)
        for t, count in sorted(by_type.items()):
            lines.append(f"  {t.upper():20s} {count}")
        lines.append("")

    if contents:
        lines.append("LISTA DE CONTEUDOS")
        lines.append("-" * 40)
        for c in contents:
            lines.append(f"  [{c.status.upper():12s}] {c.title} ({c.content_type})")
        lines.append("")

    if arts:
        lines.append("ARTES SOLICITADAS")
        lines.append("-" * 40)
        for a in arts:
            lines.append(f"  [{a.status.upper():12s}] {a.title} - Designer: {a.designer_name or 'N/A'}")
        lines.append("")

    lines.append("=" * 60)
    lines.append(f"Gerado em: {date.today().strftime('%d/%m/%Y')}")

    report_text = "\n".join(lines)
    return Response(
        content=report_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=relatorio_{month_name}_{year}.txt"},
    )
