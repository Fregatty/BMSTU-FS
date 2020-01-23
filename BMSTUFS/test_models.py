from django.test import TestCase
from .models import EducationalDepartment, Profile, Folder
from django.contrib.auth.models import User


class ModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        department = EducationalDepartment.objects.create(name='IU6')
        department.save()
        test_user = User.objects.create_superuser(username='testuser', email='1234@example.com', password='plsletmein')
        test_user.save()
        profile = Profile.objects.create(user=test_user)
        profile.save()
        folder = Folder.objects.create(name='New_folder')
        folder.save()

    def test_department_name(self):
        department = EducationalDepartment.objects.get(name='IU6').__str__()
        self.assertEqual(department, 'IU6')

    def test_profile_name(self):
        profile = Profile.objects.get(department=None)
        profile_name = profile.__str__()
        self.assertEqual(profile_name, 'Profile for user {}'.format(profile.user))

    def test_folder_path(self):
        folder = Folder.objects.get(name='New_folder')
        path = folder.get_folder_path
        self.assertEqual(path, folder.get_folder_path)

    def test_folder_get_files(self):
        folder = Folder.objects.get(name='New_folder')
        files = folder.files
        test = Folder.objects.none()
        self.assertEqual(list(files), list(test))

    def test_folder_name(self):
        folder = Folder.objects.get(name='New_folder')
        name = folder.__str__()
        self.assertEqual(name, 'New_folder')
