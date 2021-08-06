from my_app import db
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField
from decimal import Decimal
from wtforms.validators import InputRequired, NumberRange, ValidationError
from wtforms.widgets import html_params, Select, HTMLString
from flask_wtf.file import FileField, FileRequired
from flask_babel import lazy_gettext as _

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    price = db.Column(db.Float)
    category_id = db.Column(db.Integer,
        db.ForeignKey('category.id'))
    category = db.relationship(
        'Category', backref=db.backref('products', lazy='dynamic')
    )
    company = db.Column(db.String(100))
    image_path = db.Column(db.String(255))

    def __init__(self, name, price, category, image_path):
        self.image_path = image_path
        self.name = name
        self.price = price
        self.category = category
    
    def __repr__(self):
        return f'<Product {self.id}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f'<Category {self.id}>'

# class ProductForm(FlaskForm):
#     name = StringField('Name', validators=[InputRequired()])
#     price = DecimalField('Price', validators=[InputRequired(), NumberRange(min=Decimal('0.0'))])
#     category = SelectField('Category', validators=[InputRequired()], coerce=int)

def check_duplicate_category(case_sensitive=True):
    def _check_ducplicate(form, field):
        if case_sensitive:
            res = Category.query.filter(
                Category.name.like(f'%{field.data}%')
            ).first()
        else:
            res = Category.query.filter(
                Category.name.ilike(f'%field.data%')
            ).first()
        if res:
            raise ValidationError(f'Category named {field.data} already exists')
    
    return _check_ducplicate

class NameForm(FlaskForm):
    name = StringField(_('Name'), validators=[InputRequired()])

class CustomCategoryInput(Select):

    def __call__(self, field, **kwargs):
        # kwargs.setdefault('id', field.id)
        html = []
        for val, label, selected in field.iter_choices():
            html.append(
                '<input type="radio" %s> %s' % (
                    html_params(
                        name=field.name, value=val, checked=selected, **kwargs
                    ), label
                )
            )
        return HTMLString(' '.join(html))


class CategoryField(SelectField):
    widget = CustomCategoryInput()

    def iter_choices(self):
        categories = [(c.id, c.name) for c in Category.query.all()]
        for value, label in categories:
            yield (value, label, self.coerce(value) == self.data)

    def pre_validate(self, form):
        for v, _ in [(c.id, c.name) for c in Category.query.all()]:
            if self.data == v:
                break
        else:
            raise ValueError(self.gettext('Not a valid choice'))

class ProductForm(NameForm):
    price = DecimalField(_('Price'), validators=[
        InputRequired(), NumberRange(min=Decimal('0.0'))
    ])
    category = CategoryField(
        _('Category'), validators=[InputRequired()], coerce=int
    )
    image = FileField(_('Product Image'), validators=[FileRequired()])

class CategoryForm(NameForm):
    name = StringField(_('Name'), validators=[InputRequired(), check_duplicate_category()])

