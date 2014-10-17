import factory
from cards.models import WarGame


class WarGameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'cards.WarGame'

    result = WarGame.TIE
class PlayFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'cards.Player'

    username = factory.Sequence(lambda i: 'User%d' % i)
    password = factory.PostGenerationMethodCall('set_password', 'password')