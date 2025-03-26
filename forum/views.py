from django.shortcuts import render,get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Thread, Post
from .forms import ThreadForm, PostForm
from django.http import HttpResponseForbidden
# Create your views here.

def thread_list(request):
    threads = Thread.objects.all().order_by('-created_at')
    return render(request, 'forum/thread_list.html', {'threads': threads})

def thread_detail(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    posts = thread.posts.all().order_by('created_at')
    if request.method == 'POST':
        # Добавление нового сообщения
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.thread = thread
            post.author = request.user
            post.save()
            return redirect('forum:thread_detail', thread_id=thread.id)
    else:
        form = PostForm()
    return render(request, 'forum/thread_detail.html', {'thread': thread, 'posts': posts, 'form': form})

@login_required
def new_thread(request):
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            return redirect('forum:thread_list')
    else:
        form = ThreadForm()
    return render(request, 'forum/new_thread.html', {'form': form})

@login_required
def delete_thread(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
    # Разрешаем удаление только администратору (или сотруднику)
    if not request.user.is_staff:
        return HttpResponseForbidden("Вы не обладаете правами для удаления тем.")
    thread.delete()
    return redirect('forum:thread_list')

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Разрешаем удаление только администратору
    if not request.user.is_staff:
        return HttpResponseForbidden("Вы не обладаете правами для удаления сообщений.")
    # Если нужно, можно сохранить ID темы, чтобы затем вернуться на её страницу
    thread_id = post.thread.id
    post.delete()
    return redirect('forum:thread_detail', thread_id=thread_id)