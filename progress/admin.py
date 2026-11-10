from django.contrib import admin
from .models import Goal, PointsRule, Escalation, AuditLog

admin.site.register(PointsRule)
admin.site.register(AuditLog)
admin.site.register(Goal)
admin.site.register(Escalation)