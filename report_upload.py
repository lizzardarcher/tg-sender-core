import utils.djangoORM
from spambotapp.models import Message

messages = Message.objects.all()[:1000]
print('messages gathered')
groups = [x.chat for x in messages]
print(len(groups))
m_dict = {
    'group': [],
    'account': []
}
