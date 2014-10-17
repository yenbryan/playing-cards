from django.test import TestCase
from cards.factories import WarGameFactory
from cards.models import Card, Player, WarGame


class ModelTestCase(TestCase):

    def setUp(self):
        self.card = Card.objects.create(suit=Card.CLUB, rank="jack")

    def test_get_ranking(self):
        self.assertEqual(self.card.get_ranking(), 11)

    def test_get_war_result(self):
        # Test winning condition
        smaller_card = Card.objects.create(suit=Card.CLUB, rank="ten")
        self.assertEqual(self.card.get_war_result(smaller_card), 1)

        # Test tie condition
        same_card = Card.objects.create(suit=Card.CLUB, rank="jack")
        self.assertEqual(self.card.get_war_result(same_card), 0)

        # Test loosing condition
        larger_card = Card.objects.create(suit=Card.CLUB, rank="queen")
        self.assertEqual(self.card.get_war_result(larger_card), -1)

    def create_war_game(self, user, result=WarGame.LOSS):
        WarGame.objects.create(result=result, player=user)

    def test_get_wins(self):
        user = Player.objects.create_user(username='test-user', email='test@test.com', password='password')
        WarGameFactory.create_batch(2, player=user, result=WarGame.WIN)
        # self.create_war_game(user, WarGame.WIN)
        # self.create_war_game(user, WarGame.WIN)
        self.assertEqual(user.get_wins(), 2)
    #
    # def test_get_losses(self):
    #     user = Player.objects.create_user(username='test-user', email='test@test.com', password='password')
    #     self.create_war_game(user, WarGame.LOSS)
    #     self.create_war_game(user, WarGame.LOSS)
    #     self.create_war_game(user, WarGame.LOSS)
    #     self.assertEqual(user.get_losses(), 3)

    def test_get_losses(self):
        user = Player.objects.create_user(username='test-user', email='test@test.com', password='password')
        WarGameFactory.create_batch(3, player=user, result=WarGame.LOSS)
        self.assertEqual(user.get_losses(), 3)

    def test_get_ties(self):
        user = Player.objects.create_user(username='test-user', email='test@test.com', password='password')
        WarGameFactory.create_batch(4, player=user, result=WarGame.TIE)
        self.assertEqual(user.get_ties(), 4)

    def test_get_record_display(self):
        user = Player.objects.create_user(username='test-user', email='test@test.com', password='password')
        WarGameFactory.create_batch(2, player=user, result=WarGame.WIN)
        WarGameFactory.create_batch(3, player=user, result=WarGame.LOSS)
        WarGameFactory.create_batch(4, player=user, result=WarGame.TIE)
        self.assertEqual(user.get_record_display(), "2-3-4")