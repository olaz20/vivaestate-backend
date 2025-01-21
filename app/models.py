import re

from django.conf import settings
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin


class Client(TenantMixin):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    auto_create_schema = True

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Ensure schema name is set and sanitized
        if not self.schema_name:
            self.schema_name = self.name.lower().replace(
                " ", "_"
            )  # Use a sanitized version of the agency name

        # Replace any invalid characters in the schema name
        self.schema_name = re.sub(r"[^a-z0-9_]", "_", self.schema_name)

        # Ensure schema name is lowercase and clean
        self.schema_name = self.schema_name.lower()

        super(Client, self).save(*args, **kwargs)


class Domain(DomainMixin):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.domain


# Agent profile model that will be tenant-specific
class AgentProfile(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    agency_name = models.CharField(max_length=255, unique=True)
    contact_info = models.TextField()
    bio = models.TextField(blank=True)
    license_number = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (
            "client",
            "user",
        )  # Ensure each agent is unique to the tenant

    def __str__(self):
        return f"{self.agency_name} - {self.user.username}"

    def delete(self, *args, **kwargs):
        # Delete domain(s) linked to the client
        Domain.objects.filter(tenant=self.client).delete()

        # Delete the client (tenant)
        self.client.delete()

        super().delete(*args, **kwargs)
