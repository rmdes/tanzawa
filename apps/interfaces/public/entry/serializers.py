from django.utils.safestring import mark_safe
from rest_framework import serializers

import tanzawa_plugin.exercise.domain.exercise.operations
from tanzawa_plugin.exercise.data.exercise import models


class ActivityPhoto(serializers.Serializer):
    url = serializers.SerializerMethodField()

    def get_url(self, obj: models.ActivityPhoto) -> str:
        return obj.t_file.get_absolute_url()


class Activity(serializers.Serializer):
    distance_km = serializers.SerializerMethodField()
    elapsed_time_minutes = serializers.SerializerMethodField()
    average_heartrate = serializers.SerializerMethodField()
    total_elevation_gain = serializers.SerializerMethodField()
    photos = serializers.SerializerMethodField()
    route_svg = serializers.SerializerMethodField()

    def get_distance_km(self, obj: models.Activity) -> float:
        return obj.distance_km

    def get_elapsed_time_minutes(self, obj: models.Activity) -> float:
        return obj.elapsed_time_minutes

    def get_average_heartrate(self, obj: models.Activity) -> float:
        return obj.average_heartrate

    def get_total_elevation_gain(self, obj: models.Activity) -> float:
        return obj.total_elevation_gain

    def get_photos(self, obj: models.Activity) -> dict:
        return ActivityPhoto(obj.photos, many=True).data

    def get_route_svg(self, obj: models.Activity) -> str:
        return mark_safe(
            tanzawa_plugin.exercise.domain.exercise.operations.maybe_create_and_get_svg(obj, 256, 256, css_class="h-80")
        )
