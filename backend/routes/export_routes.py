from flask import Blueprint, jsonify, request, send_file, current_app
from models import db, ExportJob
import os

export_bp = Blueprint('export_bp', __name__)

@export_bp.route('/api/export-jobs', methods=['GET'])
def get_export_jobs():
    """Отримання списку завдань експорту"""
    # Опціональні параметри фільтрування та пагінації
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    
    query = ExportJob.query
    
    # Фільтрація за статусом, якщо вказаний
    if status:
        query = query.filter(ExportJob.status == status)
    
    # Пагінація та сортування за часом створення (найновіші спершу)
    paginated_jobs = query.order_by(ExportJob.created_at.desc()).paginate(
        page=page, per_page=page_size)
    
    return jsonify({
        "jobs": [job.to_dict() for job in paginated_jobs.items],
        "page": page,
        "page_size": page_size,
        "total_count": paginated_jobs.total,
        "total_pages": paginated_jobs.pages
    })

@export_bp.route('/api/export-jobs/<int:job_id>', methods=['GET'])
def get_export_job(job_id):
    """Отримання інформації про конкретне завдання експорту"""
    job = ExportJob.query.get(job_id)
    
    if not job:
        return jsonify({"error": "Export job not found"}), 404
    
    return jsonify(job.to_dict())

@export_bp.route('/api/download/<path:file_path>', methods=['GET'])
def download_file(file_path):
    """Завантаження файлу експорту"""
    # Перевіряємо, чи файл існує та чи він знаходиться в директорії експорту
    export_dir = current_app.config.get('EXPORT_DIR', 'exports')
    safe_path = os.path.normpath(os.path.join(export_dir, os.path.basename(file_path)))
    
    if not os.path.exists(safe_path) or not os.path.isfile(safe_path):
        return jsonify({"error": "File not found"}), 404
    
    # Отримуємо розширення для визначення MIME типу
    _, ext = os.path.splitext(safe_path)
    mime_type = "text/csv" if ext.lower() == ".csv" else "application/json"
    
    # Повертаємо файл для завантаження
    return send_file(
        safe_path,
        mimetype=mime_type,
        as_attachment=True,
        download_name=os.path.basename(safe_path)
    )
