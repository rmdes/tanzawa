import json

from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DeleteView, DetailView, ListView
from turbo_response.mixins import HttpResponseSeeOther, TurboFrameTemplateResponseMixin

from data.files.models import TFile
from domain.files import queries as file_queries


@method_decorator(login_required, name="dispatch")
class FilesList(TurboFrameTemplateResponseMixin, ListView):
    template_name = "files/tfiles_list.html"
    paginate_by = 20

    def get_queryset(self):
        return TFile.objects.all().order_by("-created_at")

    def get_context_data(self, *args, object_list=None, **kwargs):
        return super().get_context_data(*args, object_list=object_list, nav="files", page_title="Files")


@method_decorator(login_required, name="dispatch")
class FileDetail(TurboFrameTemplateResponseMixin, DetailView):
    template_name = "files/tfile_detail.html"
    queryset = TFile.objects.all()
    turbo_frame_dom_id = "modal"

    def get_context_data(self, **kwargs):
        kwargs["page"] = self.request.GET.get("page")
        kwargs["insert"] = self.request.GET.get("insert")
        if "turbo_frame_target" not in kwargs:
            target = self.get_turbo_frame_dom_id()
            kwargs["turbo_frame_target"] = target
        return super().get_context_data(**kwargs)

    def render_to_response(self, context, **response_kwargs):
        if self.request.turbo.frame:
            return self.render_turbo_frame(context, **response_kwargs)
        return super().render_to_response(context, **response_kwargs)


@method_decorator(login_required, name="dispatch")
class FileDelete(TurboFrameTemplateResponseMixin, DeleteView):
    queryset = TFile.objects.all()
    template_name = "files/tfile_delete.html"
    turbo_frame_dom_id = "modal"
    success_url = reverse_lazy("files")

    def render_to_response(self, context, **response_kwargs):
        if self.request.turbo.frame:
            return self.render_turbo_frame(context, **response_kwargs)
        return super().render_to_response(context, **response_kwargs)

    def get_success_url(self):
        return f"{super().get_success_url()}?page={self.request.GET.get('page')}"

    def get_context_data(self, **kwargs):
        kwargs["page"] = self.request.GET.get("page")
        return super().get_context_data(**kwargs)

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        for t_post in self.object.posts.all():
            t_entry = t_post.ref_t_entry
            soup = BeautifulSoup(t_entry.e_content, "html.parser")
            for attachment in soup.select("figure[data-trix-attachment]"):
                data = json.loads(attachment["data-trix-attachment"])
                if data["url"].endswith(self.object.get_absolute_url()):
                    attachment.decompose()
            t_entry.e_content = str(soup)
            t_entry.save()
        self.object.delete()
        success_url = self.get_success_url()
        return HttpResponseSeeOther(success_url)


@method_decorator(login_required, name="dispatch")
class FileBrowser(TurboFrameTemplateResponseMixin, ListView):
    template_name = "files/tfiles_browser.html"
    paginate_by = 20
    turbo_frame_dom_id = "modal"

    def get_queryset(self):
        return TFile.objects.all().order_by("-created_at")

    def get_context_data(self, *args, object_list=None, **kwargs):
        return super().get_context_data(*args, object_list=object_list, nav="files")

    def render_to_response(self, context, **response_kwargs):
        if self.request.turbo.frame:
            return self.render_turbo_frame(context, **response_kwargs)
        return super().render_to_response(context, **response_kwargs)


@method_decorator(login_required, name="dispatch")
class TrixFigure(DetailView):
    template_name = "trix/figure.html"
    queryset = TFile.objects.all()

    def get_context_data(self, **kwargs):
        t_file: TFile = self.object

        size = file_queries.get_size_for_file(t_file)
        img_src = file_queries.get_image_url(self.request, t_file)
        context = {
            "mime": self.object.mime_type,
            "src": img_src,
            "width": size.width,
            "height": size.height,
            "trix_attachment_data": json.dumps(
                {
                    "contentType": self.object.mime_type,
                    "filename": self.object.filename,
                    "filesize": self.object.file.size,
                    "height": size.height,
                    "href": f"{img_src}?content-disposition=attachment",
                    "url": img_src,
                    "width": size.width,
                }
            ),
        }
        return super().get_context_data(**kwargs, **context)
