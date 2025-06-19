from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
from blog.models import Post
from django.urls import reverse

class PostModelTests(TestCase):

    def setUp(self):
        # Create a dummy user for tests
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_str_representation(self):
        """Test that the __str__ method returns the post's title."""
        post = Post.objects.create(
            author=self.user,
            title='Test Title',
            text='Test content'
        )
        self.assertEqual(str(post), post.title)

    def test_publish_method(self):
        """Test that the publish method sets the published_date."""
        post = Post.objects.create(
            author=self.user,
            title='Test Publish',
            text='Test content for publish method'
        )
        self.assertIsNone(post.published_date)

        post.publish()
        post.refresh_from_db()

        self.assertIsNotNone(post.published_date)
        self.assertIsInstance(post.published_date, datetime)
        # Ensure the published_date is (almost) now.
        # We use timezone.now() as a reference, allowing for a small delta
        # because the exact microsecond might differ.
        self.assertTrue((timezone.now() - post.published_date).total_seconds() < 1)

class PostListViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')

        # Published posts
        self.published_post1 = Post.objects.create(
            author=self.user,
            title='Published Post 1',
            text='Content for published post 1.',
            published_date=timezone.now() - timedelta(days=1)
        )
        self.published_post2 = Post.objects.create(
            author=self.user,
            title='Published Post 2',
            text='Content for published post 2.',
            published_date=timezone.now() - timedelta(hours=12)
        )
        # Unpublished post
        self.unpublished_post = Post.objects.create(
            author=self.user,
            title='Unpublished Post',
            text='Content for unpublished post.'
            # published_date is None by default
        )

    def test_post_list_view_status_code(self):
        """Test the post list view returns a 200 OK status code."""
        response = self.client.get(reverse('post_list'))
        self.assertEqual(response.status_code, 200)

    def test_post_list_view_uses_correct_template(self):
        """Test the post list view uses the correct template."""
        response = self.client.get(reverse('post_list'))
        self.assertTemplateUsed(response, 'blog/post_list.html')

    def test_post_list_displays_published_posts(self):
        """Test that published posts are displayed."""
        response = self.client.get(reverse('post_list'))
        self.assertIn(self.published_post1, response.context['posts'])
        self.assertIn(self.published_post2, response.context['posts'])
        self.assertContains(response, self.published_post1.title)
        self.assertContains(response, self.published_post2.title)

    def test_post_list_does_not_display_unpublished_posts(self):
        """Test that unpublished posts are not displayed."""
        response = self.client.get(reverse('post_list'))
        self.assertNotIn(self.unpublished_post, response.context['posts'])
        self.assertNotContains(response, self.unpublished_post.title)

    def test_post_list_orders_posts_by_published_date(self):
        """Test that posts are ordered by published_date ascending."""
        # Create another published post to make ordering more robust to test
        published_post3 = Post.objects.create(
            author=self.user,
            title='Published Post 3',
            text='Content for published post 3.',
            published_date=timezone.now() - timedelta(days=2) # Oldest
        )

        response = self.client.get(reverse('post_list'))
        posts_in_context = list(response.context['posts'])

        # Expected order: published_post3 (oldest), published_post1, published_post2 (newest)
        expected_order = [published_post3, self.published_post1, self.published_post2]
        self.assertEqual(posts_in_context, expected_order)

        # Verify order in HTML content as well (more brittle, but good for sanity)
        # This checks if titles appear in the expected sequence in the response body.
        # It's a bit simplified; a more robust check might involve parsing HTML.
        response_content = response.content.decode('utf-8')
        index_post3 = response_content.find(published_post3.title)
        index_post1 = response_content.find(self.published_post1.title)
        index_post2 = response_content.find(self.published_post2.title)


        self.assertTrue(index_post3 < index_post1 < index_post2,
                        "Posts are not ordered correctly (ascending) in the rendered HTML.")
