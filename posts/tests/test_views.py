import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse
from django.test import TestCase, Client

from ..models import Post, Group, Follow, Comment


class ViewContentTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Тестовые данные"""
        cls.user = get_user_model().objects.create_user(username="Leon")
        cls.user2 = get_user_model().objects.create_user(username="Alex")

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title="Заголовок группы",
            slug="test-lev",
            description="Тестовый текст группы"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="тестовый текст поста",
            group=cls.group,
            image=uploaded
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.user
        )

    def setUp(self) -> None:
        """Тестовые пользователи"""
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_index_content(self):
        """Проверка контента index.html"""
        response = self.guest_client.get(reverse("index"))
        content = self.post
        expected_content = response.context.get("page")[0]
        self.assertEqual(content, expected_content,
                         "Контекст index.html не верен")

    def test_group_post_content(self):
        """Проверка контента group.html"""
        response = self.guest_client.get(
            reverse("group_post", args=["test-lev"]))
        content = self.post
        expected_content = response.context.get("page")[0]
        self.assertEqual(content, expected_content,
                         "Контекст group.html не верен")

    def test_post_view_content(self):
        """Проверка контента post.html"""
        response = self.authorized_user.get(
            reverse("post", kwargs={"username": self.user, "post_id": 1}))
        content = self.post
        expected_content = response.context.get("post")
        self.assertEqual(content, expected_content)

    def test_new_post_form(self):
        """Проверка полей формы для new_post add_or_change_post.html"""
        fields_list = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        response = self.authorized_user.get(reverse("new_post"))
        for field, field_widget in fields_list.items():
            form_field = response.context.get('form').fields.get(field)
            self.assertIsInstance(form_field, field_widget)

    def test_post_edit_form(self):
        """Проверка полей формы для post_edit add_or_change_post.html"""
        fields_list = {
            "text": forms.fields.CharField,
            "group": forms.fields.ChoiceField,
        }
        response = self.authorized_user.get(
            reverse("post_edit", args=["Leon", self.post.id]))

        for field, field_widget in fields_list.items():
            form_field = response.context.get('form').fields.get(field)
            self.assertIsInstance(form_field, field_widget)

    def test_create_content_index(self):
        """Тест создания поста index.html"""
        new_post = Post.objects.create(
            text="тестовый текст",
            author=self.user,
            group=self.group,
            image=self.post.image
        )
        response = self.authorized_user.get(
            reverse("index"))
        self.assertContains(response, new_post)

    def test_create_content_group(self):
        """Тест создания поста group.html"""
        new_post = Post.objects.create(
            text="тестовый текст",
            author=self.user,
            group=self.group,
            image=self.post.image
        )
        response = self.authorized_user.get(
            reverse("group_post", args=[self.group.slug]))
        self.assertContains(response, new_post)

    def test_comment_authorized_user(self):
        """Только авторизированный пользователь может комментировать пост."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Текст тестового комментария'}
        self.authorized_user.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.post.author.username,
                    'post_id': self.post.id,
                }
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1,
                         f"Комментариев меньше{comments_count + 1}")

    def test_comment_guest_client(self):
        """Неавторизированный пользователь пробует комментировать пост."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Текст тестового комментария'}
        self.guest_client.post(
            reverse(
                'add_comment',
                kwargs={
                    'username': self.post.author.username,
                    'post_id': self.post.id,
                }
            ),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comments_count,
                         "Количество комментариев больше 0")


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Тестовые данные"""
        cls.user = get_user_model().objects.create_user("Alex")

        cls.group = Group.objects.create(
            title="Заголовок группы",
            slug="test-lev",
            description="Тестовый текст группы"
        )

        for i in range(13):
            Post.objects.create(
                text=f"тестовый текст{i}",
                author=cls.user,
                group=cls.group
            )

    def setUp(self) -> None:
        self.guest_client = Client()

    def test_paginator_first_page(self):
        """Тест количества постов на странице"""
        response = self.guest_client.get(reverse("index"))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_paginator_second_page(self):
        """Тест количества постов на второй странице"""
        response = self.guest_client.get(reverse("index") + "?page=2")
        self.assertEqual(len(response.context.get('page').object_list), 3)


class FollowUserViewTest(TestCase):
    def setUp(self):
        self.author = get_user_model().objects.create(
            username='TestUserAuthor'
        )
        self.follower = get_user_model().objects.create(
            username='TestUserFollower'
        )
        self.user = get_user_model().objects.create(
            username='TestUserNOTFollower'
        )
        self.post = Post.objects.create(text="Тест",
                                        author=self.author)
        self.follow = Follow.objects.create(user=self.follower,
                                            author=self.author)

    def test_authorised_user_can_subscribe(self):
        """Тестирование подписывания на пользователей"""
        self.client.force_login(self.user)
        follow_page = reverse("profile_follow",
                              kwargs={"username": self.author.username})
        self.client.post(follow_page, follow=True)
        has_follower = Follow.objects.filter(author=self.author,
                                             user=self.user).exists()
        self.assertTrue(has_follower)

    def test_authorised_user_can_unsubscribe(self):
        """Тестирование отписывания от пользователей"""
        self.client.force_login(self.follower)
        unfollow_page = reverse("profile_unfollow",
                                kwargs={"username": self.author.username})
        self.client.post(unfollow_page, follow=True)
        no_follower = Follow.objects.filter(author=self.author,
                                            user=self.follower).exists()
        self.assertFalse(no_follower)

    def test_author_post_is_on_follower_page(self):
        """Тест страницы follow.html для подписчика"""
        self.client.force_login(self.follower)
        response = self.client.get(reverse("follow_index"))
        self.assertContains(response, self.post.text)

    def test_author_post_is_not_on_user_page(self):
        """Тест страницы follow.html для обычного пользователя"""
        self.client.force_login(self.user)
        response = self.client.get(reverse("follow_index"))
        self.assertNotContains(response, self.post.text)
