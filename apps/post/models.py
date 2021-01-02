from django.db import models

from django.contrib.auth import get_user_model

from core.models import TimestampModel


class MPostStatus(TimestampModel):

    key = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=16)

    class Meta:
        db_table = "m_post_status"

    def __str__(self):
        return self.name


class MPostKind(TimestampModel):

    key = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=16)

    class Meta:
        db_table = "m_post_kind"

    def __str__(self):
        return self.name


class TPost(TimestampModel):

    m_post_status = models.ForeignKey(MPostStatus, on_delete=models.CASCADE)
    m_post_kind = models.ForeignKey(MPostKind, on_delete=models.CASCADE)

    p_author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    published = models.DateTimeField(blank=True, null=True)
    updated = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "t_post"
