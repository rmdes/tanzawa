import mimetypes

from django.http import (FileResponse, HttpResponse, HttpResponseNotAllowed,
                         JsonResponse)
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .constants import PICTURE_FORMATS
from .forms import MediaUploadForm
from .images import convert_image_format
from .models import TFile, TFormattedImage


@csrf_exempt
def micropub_media(request):
    """
    Micropub Media Endpoint
    """
    if request.method == "POST":
        form = MediaUploadForm(request.POST, request.FILES)
        if form.is_valid():
            t_file = form.save()
            response = HttpResponse(status=201)
            response["Location"] = request.build_absolute_uri(t_file.get_absolute_url())
            return response
        return JsonResponse(
            status=400,
            data={"error": "invalid_request", "errors": form.errors.as_json()},
        )
    return HttpResponseNotAllowed(["POST"])


def get_media(request, uuid):
    t_file: TFile = get_object_or_404(TFile, uuid=uuid)
    return_file = t_file
    mime_type, _ = mimetypes.guess_type(t_file.filename)
    as_attachment = request.GET.get("content-disposition", "inline") == "attachment"
    file_format = request.GET.get("f")
    if file_format in PICTURE_FORMATS.keys():
        formatted_file = t_file.ref_t_formatted_image.filter(
            mime_type=file_format
        ).first()
        if formatted_file:
            return_file = formatted_file
        else:
            upload_file, width, height = convert_image_format(
                t_file, target_mime=file_format
            )
            if upload_file:
                formatted_file = TFormattedImage(
                    file=upload_file,
                    t_file=t_file,
                    mime_type=file_format,
                    filename=upload_file.name,
                    width=width,
                    height=height,
                )
                formatted_file.save()
                return_file = formatted_file


    response = FileResponse(
        return_file.file,
        mime_type,
        filename=return_file.filename,
        as_attachment=as_attachment,
    )
    return response
