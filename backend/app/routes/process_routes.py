from .instance_routes import instances_bp
from .task_routes import tasks_bp
from .template_routes import templates_bp


process_blueprints = [templates_bp, instances_bp, tasks_bp]
