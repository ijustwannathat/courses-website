from django.contrib.auth import authenticate, get_user_model, login
from django.core.mail import BadHeaderError, send_mail
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views import View
from taggit.models import Tag

from .forms import CommentForm, FeedBackForm, SignInForm, SignUpForm
from .models import Comment, Post


class MainView(View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all()
        paginator = Paginator(posts, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(
            request,
            "store/home.html",
            context={
                "page_obj": page_obj,
            },
        )


class PostDetailView(View):
    def get(self, request, slug, *args, **kwargs):
        post = get_object_or_404(Post, url=slug)
        common_tags = Tag.objects.annotate(num_posts=Count("post")).order_by("-id")[:5]
        last_posts = Post.objects.all().order_by("-id")[:5]
        comment_form = CommentForm()
        return render(
            request,
            "store/post_detail.html",
            context={
                "post": post,
                "common_tags": common_tags,
                "last_posts": last_posts,
                "comment_form": comment_form,
            },
        )

    def post(self, request, slug, *args, **kwargs):
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            text = request.POST["text"]
            username = self.request.user
            post = get_object_or_404(Post, url=slug)
            comment = Comment.objects.create(post=post, username=username, text=text)
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return render(
            request, "store/post_detail.html", context={"comment_form": comment_form}
        )


class SignUpView(View):
    def get(self, request, *args, **kwargs):
        form = SignUpForm()
        return render(
            request,
            "store/signup.html",
            context={
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user is not None:
                login(request, user)
                return HttpResponseRedirect("/")
        return render(
            request,
            "store/signup.html",
            context={
                "form": form,
            },
        )


class SignInView(View):
    def get(self, request, *args, **kwargs):
        form = SignInForm()
        return render(
            request,
            "store/signin.html",
            context={
                "form": form,
            },
        )

    def post(self, request, *args, **kwargs):
        form = SignInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect("/")
        return render(request, "store/signin.html", context={"form": form})


class FeedBackView(View):
    def get(self, request, *args, **kwargs):
        form = FeedBackForm()
        return render(
            request,
            "store/contact.html",
            context={
                "form": form,
                "title": "Write to me",
            },
        )

    def post(self, request, *args, **kwargs):
        form = FeedBackForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            from_email = form.cleaned_data["email"]
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            try:
                send_mail(
                    f"From{name} | {subject}",
                    message,
                    from_email,
                    ["kokfbc13@gmail.com"],
                )
            except BadHeaderError:
                return HttpResponse("Invalid title")
            return HttpResponseRedirect("success")

        return render(
            request,
            "store/contact.html",
            context={
                "form": form,
            },
        )


class FeedBackResponseView(View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            "store/appreciation.html",
            context={
                "title": "Appreciating Feedback: A Key to Growth and Success!",
            },
        )


class SearchResultsView(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("q")
        results = ""
        if query:
            results = Post.objects.filter(
                Q(h1__icontains=query) | Q(content__icontains=query)
            )
        paginator = Paginator(results, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return render(
            request,
            "store/search.html",
            context={"title": "Search", "results": page_obj, "count": results.count},
        )


class TagView(View):
    def get(self, request, slug, *args, **kwargs):
        tag = get_object_or_404(Tag, slug=slug)
        posts = Post.objects.filter(tag=tag)
        common_tags = Post.tag.most_common()
        return render(
            request,
            "store/tag.html",
            context={
                "title": f"Results by tag: {tag}",
                "posts": posts,
                "common_tags": common_tags,
            },
        )


def delete_comment(request, comment_id):
    username = request.user
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.username == username:
        comment.delete()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

