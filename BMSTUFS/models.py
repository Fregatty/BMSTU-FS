import os


from django.db import models
from django.conf import settings
# Create your models here.


# Функция для загрузки файлов по разным папкам
def get_file_path(instance, filename):
    if instance.is_in_folder:
        return '{0}/{1}/{2}'.format(instance.owner, instance.is_in_folder.get_folder_path, filename)
    else:
        return '{0}/{1}'.format(instance.owner, filename)


# Учебная кафедра
class EducationalDepartment(models.Model):
    name = models.TextField(null=False, blank=False, max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Учебная кафедра'
        verbose_name_plural = 'Учебные кафедры'


# Профиль пользователя
class Profile(models.Model):
    department_choice = []
    for f in EducationalDepartment.objects.all():
        tup = (f.id, f.name)
        department_choice.append(tup)
    department_choice.append((None, '-'))
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    department = models.ForeignKey('EducationalDepartment', on_delete=models.SET_NULL, null=True,
                                   choices=department_choice)

    def __str__(self):
        return 'Profile for user {}'.format(self.user)


# Загруженный файл
class UserFile(models.Model):
    file = models.FileField(verbose_name='Файл', upload_to=get_file_path,)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    downloaded = models.IntegerField(default=0)
    shared_to = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='shared')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='owned')
    is_in_folder = models.ForeignKey('Folder', on_delete=models.CASCADE, null=True, related_name='contains')
    belongs_to_department = models.ForeignKey(
        'EducationalDepartment',
        null=True,
        default=None,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return 'File: {0} , uploaded by {1}, downloaded {2} time(s)'.format(
            self.filename, self.owner, self.downloaded
        )

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    class Meta:
        verbose_name = 'Файл'
        verbose_name_plural = 'Файлы'


# Директория
class Folder(models.Model):
    name = models.CharField(null=False, blank=False, max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='owned_folder',
        null=True,
        blank=True
    )
    parent = models.ForeignKey(
        'self',
        verbose_name='parent',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
    )
    shared_to = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='shared_folder'
    )

    @property
    def files(self):
        return self.contains.all()

    @property
    def get_folder_path(self):
        folder_path = [self.name + '/']
        if self.parent:
            obj = self.parent
            while obj:
                folder_path.append(obj.name + '/')
                obj = obj.parent
        folder_path.reverse()
        return ''.join(folder_path)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'owner', 'parent'], name='existing_folder_constraint')
        ]


# История действий
class History(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_action')
    action = models.TextField()
    date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Действие'
        verbose_name_plural = "Действия"
