import random
from flask import Flask

from restea import errors
from restea.resource import Resource
from restea.adapters.flaskwrap import FlaskResourceWrapper
from restea import fields

app = Flask(__name__)

# Dummy data for the Resource
sites = [
    {
        'id': i,
        'name': 'my__site_{}'.format(i),
        'title': 'my site #{}'.format(i),
        'rating': random.randint(1, 5),
        'domain': 'www.my_domain_for_site_{}.com'.format(i),
        'anoher_field_out_of_scope': 'this one shouldn\'t be seen'
    } for i in range(1, 20)
]


def add_dummy_data(func):
    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        if isinstance(res, dict):
            res['dummy_key'] = 'dummy value'
        return res
    return wrapper


class SiteResource(Resource):
    decorators = [add_dummy_data]

    fields = fields.FieldSet(
        id=fields.Integer(required=True, range=(1, 100)),
        name=fields.String(max_length=50, required=True),
        title=fields.String(max_length=150),
        created_at=fields.DateTime(null=True),
    )

    def list(self):
        return sites

    def show(self, iden):
        try:
            return sites[int(iden)]
        except IndexError:
            raise errors.NotFoundError('Site doesn\'t exist', code=10)

    def edit(self, iden):
        return self.payload


with app.app_context():
    FlaskResourceWrapper(SiteResource).get_routes('/v1/sites')


if __name__ == '__main__':
    app.debug = True
    app.run()
