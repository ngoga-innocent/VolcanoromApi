from django.apps import AppConfig


class SoftwaremanagementsConfig(AppConfig):
    name = 'SoftwareManagements'
    def ready(self):
        import SoftwareManagements.signals
