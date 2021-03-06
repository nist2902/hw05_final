from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def index(request):
    """Главная страница Index"""
    post_list = Post.objects.select_related("group")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"page": page,
               "paginator": paginator, }
    return render(request, "index.html", context)


def group_posts(request, slug):
    """Страница записей сообщества group_post"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.group.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"group": group,
               "page": page,
               "paginator": paginator, }
    return render(request, "group.html", context)


@login_required
def new_post(request):
    """Страница создание поста new"""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "posts/add_or_change_post.html", {'form': form})


def profile(request, username):
    """Профайл пользователя User and Post"""
    user = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user, author=user).exists()
    )
    posts = user.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"author": user,
               "page": page,
               "paginator": paginator,
               "following": following, }
    return render(request, "posts/profile.html", context)


def post_view(request, username, post_id):
    """Просмотр записи Post"""
    post = get_object_or_404(Post, id=post_id, author__username=username)
    author_posts = post.author
    comments = post.comments.all()
    form = CommentForm()
    context = {"author": author_posts,
               "post": post,
               "form": form,
               "comments": comments, }
    return render(request, "posts/post.html", context)


@login_required
def post_edit(request, username, post_id):
    """Страница редактирования поста post_edit"""
    post = get_object_or_404(Post, id=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect("post",
                        username=request.user.username,
                        post_id=post_id)
    context = {"form": form,
               "is_edit": True,
               "post": post, }
    return render(request, 'posts/add_or_change_post.html', context)


@login_required()
def add_comment(request, username, post_id):
    """Добавление комментариев"""
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if request.GET or not form.is_valid():
        return redirect("post", post_id=post_id)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    form.save()
    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    """Страница с избранными авторами follow.html"""
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "page": page,
        "paginator": paginator,
    }
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    """Функция подписки на автора"""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Функция отписки от автора"""
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user, author=author)
    follower.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    """Страница ошибки 404"""
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    """Страница ошибки 500"""
    return render(request, "misc/500.html", status=500)
