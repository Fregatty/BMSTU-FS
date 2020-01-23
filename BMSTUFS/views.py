import datetime
import mimetypes
import os
import zipfile

from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from wsgiref.util import FileWrapper
from django.contrib import messages
from django.core.mail import EmailMessage
from django_rq import job
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from CourseFS import settings
from .models import UserFile, Folder, Profile, EducationalDepartment, History
from .forms import FileForm,  UserRegistrationForm, UserEditForm, FolderForm, EmailForm
from transliterate import translit, get_available_language_codes, detect_language


# Create your views here.


class FixedFileWrapper(FileWrapper):
    def __iter__(self):
        self.filelike.seek(0)
        return self


def index(request):
    user_count = User.objects.count()
    file_count = UserFile.objects.count()
    material_count = UserFile.objects.filter(belongs_to_department__isnull=False).count()
    return render(request, 'index.html', {'user_count': user_count, 'file_count': file_count,
                                          'material_count': material_count})


@login_required
def storage(request):
    if request.method == 'POST':
        if 'Upload' in request.POST:
            return upload_files(request, None)
        elif 'Create Folder' in request.POST:
            return create_folder(request, None)
        elif 'Delete' in request.POST:
            return delete_files(request, None)
        elif 'DeleteFolders' in request.POST:
            return delete_folder(request, None)
        elif 'Create Archive' in request.POST:
            return download_zip(request)
        elif 'Share' in request.POST:
            return share_files(request, None)
    else:
        form = FileForm()
        folder_form = FolderForm()
        documents = UserFile.objects.filter(owner=request.user, is_in_folder_id=None)
        folders = Folder.objects.filter(owner=request.user, parent=None)
        shared_files = UserFile.objects.filter(shared_to=request.user)
        department = Profile.objects.get(user=request.user).department
        department_files = UserFile.objects.filter(belongs_to_department=department)
        return render(request, 'main_storage.html', {'form': form, 'documents': documents, 'folders': folders,
                                                     'folder_form': folder_form, 'shared_files': shared_files,
                                                     'department': department, 'department_files': department_files})


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # Create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # Set the chosen password
            new_user.set_password(user_form.cleaned_data['password'])
            # Save the User object
            new_user.save()
            profile = Profile.objects.create(user=new_user, department_id=request.POST['department'])
            profile.save()
            return render(request, 'registration/register_done.html', {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'user_form': user_form})


@login_required
def edit(request):
    choices = EducationalDepartment.objects.all()
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
            profile = Profile.objects.get(user=request.user)
            profile.department_id = request.POST['department']
            profile.save()
            messages.success(request, 'Profile updated successfully')
            return render(request, 'registration/edit.html', {'user_form': user_form, 'choices': choices})
        else:
            messages.error(request, 'Error updating your profile')
            return render(request, 'registration/edit.html', {'user_form': user_form, 'choices': choices})
    else:
        user_form = UserEditForm(instance=request.user)
        return render(request,
                      'registration/edit.html',
                      {'user_form': user_form, 'choices': choices})


@login_required
def download_file(request, id):
    my_file = UserFile.objects.get(pk=id)
    my_file.downloaded += 1
    my_file.save()
    file_path = my_file.file.path
    response = HttpResponse(FixedFileWrapper(open(file_path, 'rb')), content_type=mimetypes.guess_type(file_path)[0])
    response['Content-Length'] = os.path.getsize(file_path)
    filename = my_file.filename
    if detect_language(filename) == 'ru':
        filename = translit(filename, reversed=True)
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    return response


@login_required
def recursive_zip(folder, archive, zip_subdir):
    if folder.children:
        for child in folder.children.all():
            recursive_zip(child, archive, zip_subdir)
    for f in folder.files:
        file_path = f.file.path
        f.downloaded += 1
        f.save()
        zip_add_file(file_path, zip_subdir, archive)
    return


def zip_add_file(file_path, zip_subdir, archive):
    # Calculate path for file in zip
    fdir, fname = os.path.split(file_path)
    archive_path = os.path.join(zip_subdir, fname)
    # Add file, at correct path
    archive.write(file_path, archive_path)
    return


def download_zip(request):
    selected = request.POST.getlist('selections')
    selected_folders = request.POST.getlist('folder_selections')
    response = HttpResponse(content_type='application/x-zip-compressed')
    with zipfile.ZipFile(response, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        archive.filename = date + '.zip'
        zip_subdir = date
        for pk in selected_folders:
            folder = Folder.objects.get(pk=pk)
            recursive_zip(folder, archive, zip_subdir)
        for pk in selected:
            file = UserFile.objects.get(pk=pk)
            file_path = file.file.path
            file.downloaded += 1
            file.save()
            zip_add_file(file_path, zip_subdir, archive)
    response['Content-Disposition'] = 'attachment; filename={}'.format(archive.filename)
    return response


@login_required
def show_folder(request, id):
    if request.method == 'POST':
        if 'Upload' in request.POST:
            return upload_files(request, id)
        elif 'Create Folder' in request.POST:
            return create_folder(request, id)
        elif 'Delete' in request.POST:
            return delete_files(request, id)
        elif 'DeleteFolders' in request.POST:
            return delete_folder(request, id)
        elif 'Create Archive' in request.POST:
            return download_zip(request)
        elif 'Share' in request.POST:
            return share_files(request, id)
    else:
        form = FileForm()
        folder_form = FolderForm()
        folder = Folder.objects.get(pk=id)
        children = folder.children.all()
        files = folder.files
        current_folder_id = id
        context = {'children': children,
                   'files': files,
                   'folder_id': current_folder_id,
                   'form': form,
                   'folder': folder,
                   'folder_form': folder_form,
                   }
        return render(request, 'folder_view.html', context)


@login_required
def create_folder(request, id):
    form = FolderForm(request.POST)
    if form.is_valid():
        owner = request.user
        if Folder.objects.filter(owner=owner, name=form.cleaned_data['name'], parent_id=id).count():
            messages.error(request, 'Such folder already exists, please use another name')
        else:
            folder = Folder(owner=owner, name=form.cleaned_data['name'], parent_id=id)
            folder.save()
            action = History(user=owner, action='Created folder {}'.format(folder.name))
            action.save()
    else:
        messages.error(request, 'Error while trying to create folder')
    if id:
        return HttpResponseRedirect(reverse('folder', args=[id]))
    else:
        return HttpResponseRedirect(reverse('storage'))


def upload_files(request, id):
    # Handle file upload
    form = FileForm(request.POST, request.FILES)
    files = request.FILES.getlist('file')
    if form.is_valid():
        owner = request.user
        for f in files:
            newfile = UserFile(file=f, owner=owner, is_in_folder_id=id)
            newfile.save()
            action = History(user=owner, action='Uploaded file {}'.format(newfile.filename))
            action.save()
    else:
        messages.error(request, 'File is too large (> 10 MB)')
    if id:
        return HttpResponseRedirect(reverse('folder', args=[id]))
    else:
        return HttpResponseRedirect(reverse('storage'))


def delete_files(request, id):
    selected = request.POST.getlist('selections')
    for pk in selected:
        file = UserFile.objects.get(pk=pk)
        if file.owner == request.user:
            action = History(user=request.user, action='Deleted file {}'.format(file.filename))
            action.save()
            file.file.delete()
            file.delete()
        else:
            messages.error(request, 'You don\'t have permission to delete {} file'.format(file.filename))
    if id:
        return HttpResponseRedirect(reverse('folder', args=[id]))
    else:
        return HttpResponseRedirect(reverse('storage'))


def recursive_folder(folder):
    if folder.children:
        for child in folder.children.all():
            recursive_folder(child)
    for file in folder.files:
        action = History(user=file.owner, action='Deleted file {}'.format(file.filename))
        action.save()
        file.file.delete()
        file.delete()
    action = History(user=folder.owner, action='Deleted folder {}'.format(folder.name))
    action.save()
    folder.delete()
    return


def delete_folder(request, id):
    selected_folders = request.POST.getlist('folder_selections')
    for pk in selected_folders:
        folder = Folder.objects.get(pk=pk)
        recursive_folder(folder)
    if id:
        return HttpResponseRedirect(reverse('folder', args=[id]))
    else:
        return HttpResponseRedirect(reverse('storage'))


def share_files(request, id):
    selected = request.POST.getlist('selections')
    user_name = request.POST['shared_to_user']
    if User.objects.filter(username=user_name).exists():
        for pk in selected:
            file = UserFile.objects.get(pk=pk)
            file.shared_to.add(User.objects.get(username=user_name))
        messages.success(request, 'Sharing successful')
    else:
        messages.error(request, 'Requested user doesn\'t exist')
    if id:
        return HttpResponseRedirect(reverse('folder', args=[id]))
    else:
        return HttpResponseRedirect(reverse('storage'))


def send_mail(request):
    selected = request.POST.getlist('selections')
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            msg = EmailMessage(cleaned['subject'], cleaned['body'], 'fregat3000@gmail.com', [cleaned['to']])
            msg.content_subtype = "html"
            for pk in selected:
                file = UserFile.objects.get(pk=pk).file.path
                msg.attach_file(file)
            msg.send()
            messages.success(request, "Successfully sent")
        else:
            messages.error(request, "Error, check your data")
        return HttpResponseRedirect(reverse('email'))
    else:
        form = EmailForm()
        documents = UserFile.objects.filter(owner=request.user)
        return render(request, 'send_mail.html', {'form': form, 'documents': documents})


@login_required
def show_history(request):
    if request.user.is_superuser:
        actions = History.objects.all().order_by('-date', '-user')
    else:
        actions = History.objects.filter(user=request.user).order_by('-date')
    paginator = Paginator(actions, 20)
    page = request.GET.get('page')
    try:
        actions = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        actions = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        actions = paginator.page(paginator.num_pages)
    if request.user.is_superuser:
        return render(request, 'all_history.html', {'actions': actions})
    else:
        return render(request, 'history.html', {'actions': actions})


@job
def delete_old_history():
    date = datetime.datetime.today() - datetime.timedelta(days=7)
    history = History.objects.filter(date__lte=date)
    history.delete()
    return


@user_passes_test(lambda u: u.is_superuser)
def upload_materials(request):
    choices = EducationalDepartment.objects.all()
    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        files = request.FILES.getlist('file')
        if form.is_valid():
            owner = request.user
            department = request.POST['department']
            for f in files:
                new_file = UserFile(file=f, owner=owner, belongs_to_department_id=department)
                new_file.save()
                action = History(user=owner,
                                 action='Uploaded file {0} for department {1}'.format(
                                     new_file.filename, EducationalDepartment.objects.get(pk=department).name))
                action.save()
            messages.success(request, 'Uploading successful')
        else:
            messages.error(request, 'File is too large (> 10 MB)')
    else:
        form = FileForm()
    return render(request, 'department_file.html', {'form': form, 'choices': choices})
