from django.test import TestCase
from cards.models import Card
from cards.utils import create_deck


class UtilTest(TestCase):
    def test_create_deck(self):
        self.assertEqual(Card.objects.count(), 0)
        create_deck()
        self.assertEqual(len(Card.objects.all()), 52)
