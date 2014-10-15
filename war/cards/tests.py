from time import sleep
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.test import TestCase, LiveServerTestCase
from mock import patch, Mock
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.webdriver import WebDriver
from cards.forms import EmailUserCreationForm
from cards.utils import create_deck
from cards.models import Card, Player, WarGame
from test_utils import run_pyflakes_for_package, run_pep8_for_package


class BasicMathTestCase(TestCase):
    def test_math(self):
        a = 1
        b = 1
        self.assertEqual(a + b, 2)

    # def test_failing_case(self):
    #     a = 1
    #     b = 1
    #     self.assertEqual(a+b, 1)


class ModelTestCase(TestCase):
    def setUp(self):
        self.card = Card.objects.create(suit=Card.CLUB, rank="jack")

    def create_war_game(self, user, result=WarGame.LOSS):
        WarGame.objects.create(result=result, player=user)

    def test_get_ranking(self):
        """Test that we get the proper ranking for a card"""
        self.assertEqual(self.card.get_ranking(), 11)

    def test_get_war_result_greater(self):
        first_card = Card.objects.create(suit=Card.DIAMOND, rank="five")
        second_card = Card.objects.create(suit=Card.DIAMOND, rank="four")
        self.assertEqual(first_card.get_war_result(second_card), 1)

    def test_get_war_result_equal(self):
        first_card = Card.objects.create(suit=Card.DIAMOND, rank="five")
        second_card = Card.objects.create(suit=Card.DIAMOND, rank="five")
        self.assertEqual(first_card.get_war_result(second_card), 0)

    def test_get_war_result_less(self):
        first_card = Card.objects.create(suit=Card.DIAMOND, rank="four")
        second_card = Card.objects.create(suit=Card.DIAMOND, rank="five")
        self.assertEqual(first_card.get_war_result(second_card), -1)

    def test_get_wins(self):
        user = Player.objects.create_user(username='test-user', email='test@test.com', password='password')
        self.create_war_game(user, WarGame.WIN)
        self.create_war_game(user, WarGame.WIN)
        self.assertEqual(user.get_wins(), 2)

    def test_get_losses(self):
        user = Player.objects.create_user(username='test-user', email='test@test.com', password='password')
        self.create_war_game(user, WarGame.LOSS)
        self.create_war_game(user, WarGame.LOSS)
        self.create_war_game(user, WarGame.LOSS)
        self.assertEqual(user.get_losses(), 3)


class ViewTestCase(TestCase):
    def setUp(self):
        create_deck()

    @patch('cards.utils.requests')
    def test_home_page(self, mock_requests):
        mock_comic = {
            'num': 1433,
            'year': "2014",
            'safe_title': "Lightsaber",
            'alt': "A long time in the future, in a galaxy far, far, away.",
            'transcript': "An unusual gamma-ray burst originating from somewhere far across the universe.",
            'img': "http://imgs.xkcd.com/comics/lightsaber.png",
            'title': "Lightsaber",
        }
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_comic
        mock_requests.get.return_value = mock_response

        response = self.client.get(reverse('home'))
        self.assertIn('<h3>{} - {}</h3>'.format(mock_comic['safe_title'], mock_comic['year']), response.content)
        self.assertIn('<img alt="{}" src="{}">'.format(mock_comic['alt'], mock_comic['img']), response.content)
        self.assertIn('<p>{}</p>'.format(mock_comic['transcript']), response.content)

    def test_faq_page(self):
        response = self.client.get(reverse('faq'))
        self.assertInHTML('<p>Q: Can I win real money on this website?</p>', response.content)

    def test_filters_page(self):
        response = self.client.get(reverse('filters'))
        self.assertIn('Uppercased Rank: ACE', response.content)
        self.assertEqual(response.context['cards'].count(), 52)

    def test_login_page(self):
        password = 'passsword'
        user = Player.objects.create_user(username='test-user', email='test@test.com', password=password)

        data = {
            'username': user.username,
            'password': password
        }
        self.client.post(reverse('login'), data)

    def test_register_page(self):
        username = 'new-user'
        data = {
            'username': username,
            'email': 'test@test.com',
            'password1': 'test',
            'password2': 'test'
        }
        response = self.client.post(reverse('register'), data)

        # Check this user was created in the database
        self.assertTrue(Player.objects.filter(username=username).exists())

        # Check it's a redirect to the profile page
        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertTrue(response.get('location').endswith(reverse('profile')))

    def create_war_game(self, user, result=WarGame.LOSS):
        WarGame.objects.create(result=result, player=user)

    def test_profile_page(self):
        # Create user and log them in
        password = 'passsword'
        user = Player.objects.create_user(username='test-user', email='test@test.com', password=password)
        self.client.login(username=user.username, password=password)

        # Set up some war game entries
        self.create_war_game(user)
        self.create_war_game(user)
        self.create_war_game(user)
        self.create_war_game(user, WarGame.WIN)
        self.create_war_game(user, WarGame.WIN)

        # Make the url call and check the html and games queryset length
        response = self.client.get(reverse('profile'))
        self.assertInHTML('<p>Hi {}, you have 2 wins and 3 losses.</p>'.format(user.username), response.content)
        self.assertEqual(len(response.context['games']), 5)
        self.assertEqual(response.context['wins'], 2)
        self.assertEqual(response.context['losses'], 3)


class UtilTestCase(TestCase):
    def test_create_deck_count(self):
        """Test that we created 52 cards"""
        create_deck()
        self.assertEqual(Card.objects.count(), 52)


class FormTestCase(TestCase):
    def test_clean_username_exception(self):
        # Create a player so that this username we're testing is already taken
        Player.objects.create_user(username='test-user')

        # set up the form for testing
        form = EmailUserCreationForm()
        form.cleaned_data = {'username': 'test-user'}

        # use a context manager to watch for the validation error being raised
        with self.assertRaises(ValidationError):
            form.clean_username()

    def test_clean_username(self):
        # set up the form for testing
        form = EmailUserCreationForm()
        form.cleaned_data = {'username': 'test-user'}
        self.assertEquals(form.clean_username(), 'test-user')

    def test_register_sends_email(self):
        form = EmailUserCreationForm()
        form.cleaned_data = {
            'username': 'test',
            'email': 'test@test.com',
            'password1': 'test-pw',
            'password2': 'test-pw',
        }
        form.save()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Welcome!')


class TemplateTagTestCase(TestCase):
    pass


class SyntaxTest(TestCase):
    def test_syntax(self):
        """
        Run pyflakes/pep8 across the code base to check for potential errors.
        """
        packages = ['cards']
        warnings = []
        # Eventually should use flake8 instead so we can ignore specific lines via a comment
        for package in packages:
            warnings.extend(run_pyflakes_for_package(package, extra_ignore=("_settings",)))
            warnings.extend(run_pep8_for_package(package, extra_ignore=("_settings",)))
        if warnings:
            self.fail("{0} Syntax warnings!\n\n{1}".format(len(warnings), "\n".join(warnings)))


class SeleniumTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.selenium = WebDriver()
        super(SeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTests, cls).tearDownClass()

    def admin_login(self):
        # Create a superuser
        Player.objects.create_superuser('superuser', 'superuser@test.com', 'mypassword')

        # let's open the admin login page
        self.selenium.get("{}{}".format(self.live_server_url, reverse('admin:index')))

        # let's fill out the form with our superuser's username and password
        self.selenium.find_element_by_name('username').send_keys('superuser')
        password_input = self.selenium.find_element_by_name('password')
        password_input.send_keys('mypassword')

        # Submit the form
        password_input.send_keys(Keys.RETURN)

    def test_admin_login(self):
        # Create a superuser
        Player.objects.create_superuser('superuser', 'superuser@test.com', 'mypassword')

        # let's open the admin login page
        self.selenium.get("{}{}".format(self.live_server_url, reverse('admin:index')))

        # let's fill out the form with our superuser's username and password
        self.selenium.find_element_by_name('username').send_keys('superuser')
        password_input = self.selenium.find_element_by_name('password')
        password_input.send_keys('mypassword')

        # Submit the form
        password_input.send_keys(Keys.RETURN)

        # sleep for half a second to let the page load
        sleep(.5)

        # We check to see if 'Site administration' is now on the page, this means we logged in successfully
        body = self.selenium.find_element_by_tag_name('body')
        self.assertIn('Site administration', body.text)

    def test_admin_create_card(self):
        self.admin_login()

        # We can check that our Card model is registered with the admin and we can click on it
        # Get the 2nd one, since the first is the header
        self.selenium.find_elements_by_link_text('Cards')[1].click()

        # Let's click to add a new card
        self.selenium.find_element_by_link_text('Add card').click()

        # Let's fill out the card form
        self.selenium.find_element_by_name('rank').send_keys("ace")
        suit_dropdown = self.selenium.find_element_by_name('suit')
        for option in suit_dropdown.find_elements_by_tag_name('option'):
            if option.text == "heart":
                option.click()

        # Click save to create the new card
        self.selenium.find_element_by_css_selector("input[value='Save']").click()

        sleep(.5)

        # Check to see we get the card was added success message
        body = self.selenium.find_element_by_tag_name('body')
        self.assertIn('The card "ace of hearts" was added successfully', body.text)
